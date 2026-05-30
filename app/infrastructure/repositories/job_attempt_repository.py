from uuid import UUID

from sqlalchemy import desc, select, update
from sqlalchemy.orm import Session

from app.core.time import milliseconds_between, utc_now
from app.domain.jobs.entities import JobAttempt
from app.domain.jobs.enums import AttemptStatus
from app.infrastructure.database.models.job_attempt_model import JobAttemptModel


class JobAttemptRepository:
    """
    Repository for job attempt persistence operations.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_attempt(
        self,
        *,
        job_id: UUID,
        attempt_number: int,
        worker_id: str,
        worker_run_id: str,
    ) -> JobAttempt:
        """
        Create a STARTED attempt for a job.
        """
        now = utc_now()

        model = JobAttemptModel(
            job_id=job_id,
            attempt_number=attempt_number,
            worker_id=worker_id,
            worker_run_id=worker_run_id,
            status=AttemptStatus.STARTED.value,
            started_at=now,
            created_at=now,
        )

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def list_by_job_id(self, job_id: UUID) -> list[JobAttempt]:
        """
        List all attempts for a job ordered by attempt number.
        """
        stmt = (
            select(JobAttemptModel)
            .where(JobAttemptModel.job_id == job_id)
            .order_by(JobAttemptModel.attempt_number)
        )

        models = self.session.scalars(stmt).all()

        return [self._to_domain(model) for model in models]

    def get_latest_started_attempt(self, job_id: UUID) -> JobAttempt | None:
        """
        Return the latest STARTED attempt for a job.

        This is useful for stale recovery when a worker crashed before finishing
        the attempt.
        """
        stmt = (
            select(JobAttemptModel)
            .where(
                JobAttemptModel.job_id == job_id,
                JobAttemptModel.status == AttemptStatus.STARTED.value,
            )
            .order_by(desc(JobAttemptModel.attempt_number))
            .limit(1)
        )

        model = self.session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_domain(model)

    def mark_succeeded(
        self,
        *,
        attempt_id: UUID,
    ) -> bool:
        """
        Mark an attempt as SUCCEEDED.
        """
        now = utc_now()

        model = self.session.get(JobAttemptModel, attempt_id)

        if model is None:
            return False

        duration_ms = milliseconds_between(model.started_at, now)

        stmt = (
            update(JobAttemptModel)
            .where(
                JobAttemptModel.id == attempt_id,
                JobAttemptModel.status == AttemptStatus.STARTED.value,
            )
            .values(
                status=AttemptStatus.SUCCEEDED.value,
                finished_at=now,
                duration_ms=duration_ms,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def mark_failed(
        self,
        *,
        attempt_id: UUID,
        error_type: str,
        error_message: str,
    ) -> bool:
        """
        Mark an attempt as FAILED.
        """
        now = utc_now()

        model = self.session.get(JobAttemptModel, attempt_id)

        if model is None:
            return False

        duration_ms = milliseconds_between(model.started_at, now)

        stmt = (
            update(JobAttemptModel)
            .where(
                JobAttemptModel.id == attempt_id,
                JobAttemptModel.status == AttemptStatus.STARTED.value,
            )
            .values(
                status=AttemptStatus.FAILED.value,
                finished_at=now,
                duration_ms=duration_ms,
                error_type=error_type,
                error_message=error_message,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def mark_timed_out(
        self,
        *,
        attempt_id: UUID,
        error_type: str,
        error_message: str,
    ) -> bool:
        """
        Mark an attempt as TIMED_OUT.
        """
        now = utc_now()

        model = self.session.get(JobAttemptModel, attempt_id)

        if model is None:
            return False

        duration_ms = milliseconds_between(model.started_at, now)

        stmt = (
            update(JobAttemptModel)
            .where(
                JobAttemptModel.id == attempt_id,
                JobAttemptModel.status == AttemptStatus.STARTED.value,
            )
            .values(
                status=AttemptStatus.TIMED_OUT.value,
                finished_at=now,
                duration_ms=duration_ms,
                error_type=error_type,
                error_message=error_message,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def mark_latest_started_attempt_timed_out(
        self,
        *,
        job_id: UUID,
        error_type: str,
        error_message: str,
    ) -> bool:
        """
        Mark the latest STARTED attempt for a job as TIMED_OUT.

        Used by stale recovery.
        """
        latest_attempt = self.get_latest_started_attempt(job_id)

        if latest_attempt is None:
            return False

        return self.mark_timed_out(
            attempt_id=latest_attempt.id,
            error_type=error_type,
            error_message=error_message,
        )

    def _to_domain(self, model: JobAttemptModel) -> JobAttempt:
        """
        Convert a SQLAlchemy model into a domain JobAttempt entity.
        """
        return JobAttempt(
            id=model.id,
            job_id=model.job_id,
            attempt_number=model.attempt_number,
            worker_id=model.worker_id,
            worker_run_id=model.worker_run_id,
            status=AttemptStatus(model.status),
            started_at=model.started_at,
            finished_at=model.finished_at,
            duration_ms=model.duration_ms,
            error_type=model.error_type,
            error_message=model.error_message,
            created_at=model.created_at,
        )