import logging
import time

from app.handlers.registry import HandlerRegistry
from app.infrastructure.database.session import create_db_session
from app.infrastructure.repositories.email_delivery_repository import (
    EmailDeliveryRepository,
)
from app.infrastructure.repositories.job_attempt_repository import (
    JobAttemptRepository,
)
from app.infrastructure.repositories.job_repository import JobRepository
from app.observability.events import LogEvent
from app.observability.logging import get_logger, log_event
from app.worker.config import WorkerConfig
from app.worker.job_processor import JobProcessor
from app.worker.worker_identity import WorkerIdentity


logger = get_logger(__name__)


class Worker:
    """
    Polling worker that claims and processes background jobs.
    """

    def __init__(
        self,
        *,
        config: WorkerConfig,
        identity: WorkerIdentity,
    ) -> None:
        self.config = config
        self.identity = identity
        self._should_stop = False

    def run_forever(self) -> None:
        """
        Run the worker loop forever until stopped.

        This is intentionally simple for v1.
        """
        log_event(
            logger,
            logging.INFO,
            LogEvent.WORKER_STARTED,
            worker_id=self.identity.worker_id,
            worker_run_id=self.identity.worker_run_id,
            queue_name=self.config.queue_name,
            batch_size=self.config.batch_size,
        )

        while not self._should_stop:
            processed_count = self.poll_once()

            if processed_count == 0:
                time.sleep(self.config.poll_interval_seconds)

        log_event(
            logger,
            logging.INFO,
            LogEvent.WORKER_STOPPED,
            worker_id=self.identity.worker_id,
            worker_run_id=self.identity.worker_run_id,
        )

    def stop(self) -> None:
        """
        Request the worker loop to stop.
        """
        self._should_stop = True

    def poll_once(self) -> int:
        """
        Claim and process one batch of jobs.

        Returns the number of jobs claimed.
        """
        session = create_db_session()

        try:
            job_repository = JobRepository(session)

            jobs = job_repository.claim_available_jobs(
                queue_name=self.config.queue_name,
                worker_id=self.identity.worker_id,
                worker_run_id=self.identity.worker_run_id,
                batch_size=self.config.batch_size,
                lock_timeout_seconds=self.config.lock_timeout_seconds,
            )

            session.commit()

            if not jobs:
                return 0

            log_event(
                logger,
                logging.INFO,
                LogEvent.JOB_CLAIMED,
                worker_id=self.identity.worker_id,
                worker_run_id=self.identity.worker_run_id,
                queue_name=self.config.queue_name,
                claimed_count=len(jobs),
            )

        except Exception as exc:
            session.rollback()

            log_event(
                logger,
                logging.ERROR,
                "job_claim_batch_failed",
                worker_id=self.identity.worker_id,
                worker_run_id=self.identity.worker_run_id,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )

            return 0

        finally:
            session.close()

        for job in jobs:
            self._process_claimed_job(job)

        return len(jobs)

    def _process_claimed_job(self, job) -> None:
        """
        Process one already-claimed job in its own database session.
        """
        session = create_db_session()

        try:
            job_repository = JobRepository(session)
            attempt_repository = JobAttemptRepository(session)
            email_delivery_repository = EmailDeliveryRepository(session)

            handler_registry = HandlerRegistry(
                email_delivery_repository=email_delivery_repository,
            )

            processor = JobProcessor(
                job_repository=job_repository,
                job_attempt_repository=attempt_repository,
                handler_registry=handler_registry,
                worker_identity=self.identity,
            )

            processor.process(job)
            session.commit()

        except Exception as exc:
            session.rollback()

            log_event(
                logger,
                logging.ERROR,
                "job_processing_top_level_failed",
                job_id=job.id,
                worker_id=self.identity.worker_id,
                worker_run_id=self.identity.worker_run_id,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )

        finally:
            session.close()