import logging

from app.core.config import get_settings
from app.domain.jobs.entities import Job
from app.domain.jobs.errors import (
    AmbiguousJobError,
    JobError,
    LockLostError,
    NonRetryableJobError,
    RetryableJobError,
)
from app.domain.jobs.retry_policy import RetryPolicy
from app.handlers.registry import HandlerRegistry
from app.infrastructure.repositories.job_attempt_repository import (
    JobAttemptRepository,
)
from app.infrastructure.repositories.job_repository import JobRepository
from app.observability.events import LogEvent
from app.observability.logging import get_logger, log_event
from app.worker.worker_identity import WorkerIdentity


logger = get_logger(__name__)


class JobProcessor:
    """
    Coordinates the execution of one job.

    The processor does not know job-type-specific business logic.
    It delegates execution to handlers and owns lifecycle decisions.
    """

    def __init__(
        self,
        *,
        job_repository: JobRepository,
        job_attempt_repository: JobAttemptRepository,
        handler_registry: HandlerRegistry,
        worker_identity: WorkerIdentity,
    ) -> None:
        self.job_repository = job_repository
        self.job_attempt_repository = job_attempt_repository
        self.handler_registry = handler_registry
        self.worker_identity = worker_identity

        settings = get_settings()
        self.retry_policy = RetryPolicy(
            base_delay_seconds=settings.retry_base_delay_seconds,
            max_delay_seconds=settings.retry_max_delay_seconds,
            jitter_ratio=settings.retry_jitter_ratio,
        )

    def process(self, job: Job) -> None:
        """
        Process one claimed job.

        The job is expected to already be RUNNING and owned by this worker.
        """
        attempt = self.job_attempt_repository.create_attempt(
            job_id=job.id,
            attempt_number=job.attempt_count,
            worker_id=self.worker_identity.worker_id,
            worker_run_id=self.worker_identity.worker_run_id,
        )

        log_event(
            logger,
            logging.INFO,
            LogEvent.JOB_ATTEMPT_STARTED,
            job_id=job.id,
            attempt_id=attempt.id,
            attempt_number=attempt.attempt_number,
            worker_id=self.worker_identity.worker_id,
            worker_run_id=self.worker_identity.worker_run_id,
            job_type=job.type.value,
            queue_name=job.queue_name,
        )

        try:
            handler = self.handler_registry.get(job.type)
            result = handler.handle(job)

            self.job_attempt_repository.mark_succeeded(
                attempt_id=attempt.id,
            )

            updated = self.job_repository.mark_succeeded_if_owned(
                job_id=job.id,
                worker_id=self.worker_identity.worker_id,
                worker_run_id=self.worker_identity.worker_run_id,
            )

            if not updated:
                raise LockLostError(
                    "Worker lost job ownership before marking job as succeeded",
                    code="LOCK_LOST_ON_SUCCESS",
                )

            log_event(
                logger,
                logging.INFO,
                LogEvent.JOB_SUCCEEDED,
                job_id=job.id,
                attempt_id=attempt.id,
                worker_id=self.worker_identity.worker_id,
                worker_run_id=self.worker_identity.worker_run_id,
                message=result.message,
            )

        except RetryableJobError as exc:
            self._handle_retryable_failure(
                job=job,
                attempt_id=attempt.id,
                exc=exc,
            )

        except AmbiguousJobError as exc:
            self._handle_ambiguous_failure(
                job=job,
                attempt_id=attempt.id,
                exc=exc,
            )

        except NonRetryableJobError as exc:
            self._handle_non_retryable_failure(
                job=job,
                attempt_id=attempt.id,
                exc=exc,
            )

        except LockLostError as exc:
            self.job_attempt_repository.mark_failed(
                attempt_id=attempt.id,
                error_type=exc.code,
                error_message=exc.message,
            )

            log_event(
                logger,
                logging.WARNING,
                LogEvent.HEARTBEAT_LOST,
                job_id=job.id,
                attempt_id=attempt.id,
                worker_id=self.worker_identity.worker_id,
                worker_run_id=self.worker_identity.worker_run_id,
                error_type=exc.code,
                error_message=exc.message,
            )

        except Exception as exc:
            self._handle_unexpected_failure(
                job=job,
                attempt_id=attempt.id,
                exc=exc,
            )

    def _handle_retryable_failure(
        self,
        *,
        job: Job,
        attempt_id,
        exc: RetryableJobError,
    ) -> None:
        """
        Handle a failure that may succeed later.
        """
        self.job_attempt_repository.mark_failed(
            attempt_id=attempt_id,
            error_type=exc.code,
            error_message=exc.message,
        )

        if job.has_attempts_remaining:
            next_available_at = self.retry_policy.get_next_available_at(
                attempt_count=job.attempt_count,
            )

            updated = self.job_repository.schedule_retry_if_owned(
                job_id=job.id,
                worker_id=self.worker_identity.worker_id,
                worker_run_id=self.worker_identity.worker_run_id,
                available_at=next_available_at,
                error_type=exc.code,
                error_message=exc.message,
            )

            if not updated:
                raise LockLostError(
                    "Worker lost job ownership before scheduling retry",
                    code="LOCK_LOST_ON_RETRY",
                )

            log_event(
                logger,
                logging.WARNING,
                LogEvent.JOB_RETRY_SCHEDULED,
                job_id=job.id,
                attempt_id=attempt_id,
                worker_id=self.worker_identity.worker_id,
                worker_run_id=self.worker_identity.worker_run_id,
                error_type=exc.code,
                next_available_at=next_available_at,
            )

            return

        self._move_to_dead_letter(
            job=job,
            attempt_id=attempt_id,
            error_type=exc.code,
            error_message=exc.message,
        )

    def _handle_non_retryable_failure(
        self,
        *,
        job: Job,
        attempt_id,
        exc: NonRetryableJobError,
    ) -> None:
        """
        Handle a permanent failure.
        """
        self.job_attempt_repository.mark_failed(
            attempt_id=attempt_id,
            error_type=exc.code,
            error_message=exc.message,
        )

        self._move_to_dead_letter(
            job=job,
            attempt_id=attempt_id,
            error_type=exc.code,
            error_message=exc.message,
        )

    def _handle_ambiguous_failure(
        self,
        *,
        job: Job,
        attempt_id,
        exc: AmbiguousJobError,
    ) -> None:
        """
        Handle an ambiguous external side-effect failure.

        For v1, we retry while attempts remain. The handler itself must avoid
        blindly repeating unsafe side effects when local state is UNKNOWN.
        """
        self.job_attempt_repository.mark_failed(
            attempt_id=attempt_id,
            error_type=exc.code,
            error_message=exc.message,
        )

        if job.has_attempts_remaining:
            next_available_at = self.retry_policy.get_next_available_at(
                attempt_count=job.attempt_count,
            )

            updated = self.job_repository.schedule_retry_if_owned(
                job_id=job.id,
                worker_id=self.worker_identity.worker_id,
                worker_run_id=self.worker_identity.worker_run_id,
                available_at=next_available_at,
                error_type=exc.code,
                error_message=exc.message,
            )

            if not updated:
                raise LockLostError(
                    "Worker lost job ownership before scheduling ambiguous retry",
                    code="LOCK_LOST_ON_AMBIGUOUS_RETRY",
                )

            log_event(
                logger,
                logging.WARNING,
                LogEvent.JOB_RETRY_SCHEDULED,
                job_id=job.id,
                attempt_id=attempt_id,
                worker_id=self.worker_identity.worker_id,
                worker_run_id=self.worker_identity.worker_run_id,
                error_type=exc.code,
                ambiguous=True,
                next_available_at=next_available_at,
            )

            return

        self._move_to_dead_letter(
            job=job,
            attempt_id=attempt_id,
            error_type=exc.code,
            error_message=exc.message,
        )

    def _handle_unexpected_failure(
        self,
        *,
        job: Job,
        attempt_id,
        exc: Exception,
    ) -> None:
        """
        Handle an unexpected exception.

        In v1, unexpected failures are treated as retryable until attempts are
        exhausted.
        """
        error_type = exc.__class__.__name__
        error_message = str(exc) or "Unexpected job failure"

        self.job_attempt_repository.mark_failed(
            attempt_id=attempt_id,
            error_type=error_type,
            error_message=error_message,
        )

        if job.has_attempts_remaining:
            next_available_at = self.retry_policy.get_next_available_at(
                attempt_count=job.attempt_count,
            )

            updated = self.job_repository.schedule_retry_if_owned(
                job_id=job.id,
                worker_id=self.worker_identity.worker_id,
                worker_run_id=self.worker_identity.worker_run_id,
                available_at=next_available_at,
                error_type=error_type,
                error_message=error_message,
            )

            if not updated:
                raise LockLostError(
                    "Worker lost job ownership before scheduling retry after unexpected failure",
                    code="LOCK_LOST_ON_UNEXPECTED_RETRY",
                )

            log_event(
                logger,
                logging.ERROR,
                LogEvent.JOB_RETRY_SCHEDULED,
                job_id=job.id,
                attempt_id=attempt_id,
                worker_id=self.worker_identity.worker_id,
                worker_run_id=self.worker_identity.worker_run_id,
                error_type=error_type,
                next_available_at=next_available_at,
            )

            return

        self._move_to_dead_letter(
            job=job,
            attempt_id=attempt_id,
            error_type=error_type,
            error_message=error_message,
        )

    def _move_to_dead_letter(
        self,
        *,
        job: Job,
        attempt_id,
        error_type: str,
        error_message: str,
    ) -> None:
        """
        Move a job to DEAD_LETTER if this worker still owns it.
        """
        updated = self.job_repository.move_to_dead_letter_if_owned(
            job_id=job.id,
            worker_id=self.worker_identity.worker_id,
            worker_run_id=self.worker_identity.worker_run_id,
            error_type=error_type,
            error_message=error_message,
        )

        if not updated:
            raise LockLostError(
                "Worker lost job ownership before moving job to dead-letter",
                code="LOCK_LOST_ON_DEAD_LETTER",
            )

        log_event(
            logger,
            logging.ERROR,
            LogEvent.JOB_DEAD_LETTERED,
            job_id=job.id,
            attempt_id=attempt_id,
            worker_id=self.worker_identity.worker_id,
            worker_run_id=self.worker_identity.worker_run_id,
            error_type=error_type,
        )