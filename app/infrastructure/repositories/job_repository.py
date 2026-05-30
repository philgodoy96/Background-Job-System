from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, and_, desc, select, update
from sqlalchemy.orm import Session

from app.core.time import seconds_from_now, utc_now
from app.domain.jobs.entities import Job
from app.domain.jobs.enums import JobStatus, JobType
from app.infrastructure.database.models.job_model import JobModel


class JobRepository:
    """
    Repository for job persistence operations.

    This repository owns database-safe job operations such as claiming,
    lock renewal, lifecycle updates, and stale job discovery.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_job(
        self,
        *,
        job_type: JobType,
        queue_name: str,
        payload: dict,
        idempotency_key: str | None,
        priority: int,
        available_at: datetime | None,
        max_attempts: int,
    ) -> Job:
        """
        Create a new job in PENDING status.
        """
        now = utc_now()

        model = JobModel(
            type=job_type.value,
            queue_name=queue_name,
            status=JobStatus.PENDING.value,
            payload=payload,
            idempotency_key=idempotency_key,
            priority=priority,
            available_at=available_at or now,
            attempt_count=0,
            max_attempts=max_attempts,
            created_at=now,
            updated_at=now,
        )

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def get_by_id(self, job_id: UUID) -> Job | None:
        """
        Return a job by id, or None if it does not exist.
        """
        model = self.session.get(JobModel, job_id)

        if model is None:
            return None

        return self._to_domain(model)

    def list_jobs(
        self,
        *,
        status: JobStatus | None = None,
        queue_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        """
        List jobs for API queries.
        """
        stmt: Select[tuple[JobModel]] = select(JobModel)

        if status is not None:
            stmt = stmt.where(JobModel.status == status.value)

        if queue_name is not None:
            stmt = stmt.where(JobModel.queue_name == queue_name)

        stmt = (
            stmt.order_by(desc(JobModel.created_at))
            .limit(limit)
            .offset(offset)
        )

        models = self.session.scalars(stmt).all()

        return [self._to_domain(model) for model in models]

    def claim_available_jobs(
        self,
        *,
        queue_name: str,
        worker_id: str,
        worker_run_id: str,
        batch_size: int,
        lock_timeout_seconds: int,
    ) -> list[Job]:
        """
        Claim available jobs safely using row-level locking.

        This method uses SELECT FOR UPDATE SKIP LOCKED so that multiple workers
        can claim jobs concurrently without claiming the same rows.
        """
        now = utc_now()
        locked_until = seconds_from_now(lock_timeout_seconds)

        stmt = (
            select(JobModel)
            .where(
                JobModel.queue_name == queue_name,
                JobModel.status.in_(
                    [
                        JobStatus.PENDING.value,
                        JobStatus.RETRY_SCHEDULED.value,
                    ]
                ),
                JobModel.available_at <= now,
            )
            .order_by(
                desc(JobModel.priority),
                JobModel.available_at,
                JobModel.created_at,
            )
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )

        models = list(self.session.scalars(stmt).all())

        for model in models:
            model.status = JobStatus.RUNNING.value
            model.locked_by = worker_id
            model.locked_by_run_id = worker_run_id
            model.locked_until = locked_until
            model.attempt_count += 1
            model.updated_at = now

        self.session.flush()

        return [self._to_domain(model) for model in models]

    def renew_lock(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        worker_run_id: str,
        lock_timeout_seconds: int,
    ) -> bool:
        """
        Renew a job lock only if the worker still owns the job.

        Returns True if the lock was renewed.
        Returns False if the worker has lost ownership.
        """
        now = utc_now()
        new_locked_until = seconds_from_now(lock_timeout_seconds)

        stmt = (
            update(JobModel)
            .where(
                JobModel.id == job_id,
                JobModel.status == JobStatus.RUNNING.value,
                JobModel.locked_by == worker_id,
                JobModel.locked_by_run_id == worker_run_id,
            )
            .values(
                locked_until=new_locked_until,
                updated_at=now,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def mark_succeeded_if_owned(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        worker_run_id: str,
    ) -> bool:
        """
        Mark a job as SUCCEEDED only if the worker still owns it.
        """
        now = utc_now()

        stmt = (
            update(JobModel)
            .where(
                JobModel.id == job_id,
                JobModel.status == JobStatus.RUNNING.value,
                JobModel.locked_by == worker_id,
                JobModel.locked_by_run_id == worker_run_id,
            )
            .values(
                status=JobStatus.SUCCEEDED.value,
                locked_by=None,
                locked_by_run_id=None,
                locked_until=None,
                completed_at=now,
                updated_at=now,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def schedule_retry_if_owned(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        worker_run_id: str,
        available_at: datetime,
        error_type: str,
        error_message: str,
    ) -> bool:
        """
        Move a RUNNING job to RETRY_SCHEDULED only if the worker still owns it.
        """
        now = utc_now()

        stmt = (
            update(JobModel)
            .where(
                JobModel.id == job_id,
                JobModel.status == JobStatus.RUNNING.value,
                JobModel.locked_by == worker_id,
                JobModel.locked_by_run_id == worker_run_id,
            )
            .values(
                status=JobStatus.RETRY_SCHEDULED.value,
                available_at=available_at,
                locked_by=None,
                locked_by_run_id=None,
                locked_until=None,
                last_error_type=error_type,
                last_error_message=error_message,
                updated_at=now,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def move_to_dead_letter_if_owned(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        worker_run_id: str,
        error_type: str,
        error_message: str,
    ) -> bool:
        """
        Move a RUNNING job to DEAD_LETTER only if the worker still owns it.
        """
        now = utc_now()

        stmt = (
            update(JobModel)
            .where(
                JobModel.id == job_id,
                JobModel.status == JobStatus.RUNNING.value,
                JobModel.locked_by == worker_id,
                JobModel.locked_by_run_id == worker_run_id,
            )
            .values(
                status=JobStatus.DEAD_LETTER.value,
                locked_by=None,
                locked_by_run_id=None,
                locked_until=None,
                last_error_type=error_type,
                last_error_message=error_message,
                completed_at=now,
                updated_at=now,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def find_stale_running_jobs(
        self,
        *,
        limit: int,
    ) -> list[Job]:
        """
        Find RUNNING jobs whose locks have expired.

        These jobs were likely abandoned by crashed workers or workers that
        stopped renewing heartbeat.
        """
        now = utc_now()

        stmt = (
            select(JobModel)
            .where(
                JobModel.status == JobStatus.RUNNING.value,
                JobModel.locked_until.is_not(None),
                JobModel.locked_until < now,
            )
            .order_by(JobModel.locked_until)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        models = list(self.session.scalars(stmt).all())

        return [self._to_domain(model) for model in models]

    def reschedule_stale_job(
        self,
        *,
        job_id: UUID,
        available_at: datetime,
        error_type: str,
        error_message: str,
    ) -> bool:
        """
        Reschedule a stale RUNNING job for retry.

        This is used by the recovery process after detecting that locked_until
        has expired.
        """
        now = utc_now()

        stmt = (
            update(JobModel)
            .where(
                JobModel.id == job_id,
                JobModel.status == JobStatus.RUNNING.value,
                JobModel.locked_until.is_not(None),
                JobModel.locked_until < now,
            )
            .values(
                status=JobStatus.RETRY_SCHEDULED.value,
                available_at=available_at,
                locked_by=None,
                locked_by_run_id=None,
                locked_until=None,
                last_error_type=error_type,
                last_error_message=error_message,
                updated_at=now,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def move_stale_job_to_dead_letter(
        self,
        *,
        job_id: UUID,
        error_type: str,
        error_message: str,
    ) -> bool:
        """
        Move a stale RUNNING job to DEAD_LETTER.

        This is used by recovery when the job has exhausted attempts.
        """
        now = utc_now()

        stmt = (
            update(JobModel)
            .where(
                JobModel.id == job_id,
                JobModel.status == JobStatus.RUNNING.value,
                JobModel.locked_until.is_not(None),
                JobModel.locked_until < now,
            )
            .values(
                status=JobStatus.DEAD_LETTER.value,
                locked_by=None,
                locked_by_run_id=None,
                locked_until=None,
                last_error_type=error_type,
                last_error_message=error_message,
                completed_at=now,
                updated_at=now,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def _to_domain(self, model: JobModel) -> Job:
        """
        Convert a SQLAlchemy model into a domain Job entity.
        """
        return Job(
            id=model.id,
            type=JobType(model.type),
            queue_name=model.queue_name,
            status=JobStatus(model.status),
            payload=model.payload,
            idempotency_key=model.idempotency_key,
            priority=model.priority,
            available_at=model.available_at,
            attempt_count=model.attempt_count,
            max_attempts=model.max_attempts,
            locked_by=model.locked_by,
            locked_by_run_id=model.locked_by_run_id,
            locked_until=model.locked_until,
            last_error_type=model.last_error_type,
            last_error_message=model.last_error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at,
        )