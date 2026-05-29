import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.domain.jobs.enums import FailureType, JobStatus, JobType
from app.infrastructure.database.models import JobModel


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        job_type: JobType,
        queue_name: str,
        payload: dict[str, Any],
        idempotency_key: str | None,
        priority: int,
        available_at: datetime,
        max_attempts: int,
    ) -> JobModel:
        job = JobModel(
            type=job_type.value,
            queue_name=queue_name,
            status=JobStatus.PENDING.value,
            payload=payload,
            idempotency_key=idempotency_key,
            priority=priority,
            available_at=available_at,
            attempt_count=0,
            max_attempts=max_attempts,
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return job

    def get_by_id(self, job_id: uuid.UUID) -> JobModel | None:
        return self.db.get(JobModel, job_id)

    def list(
        self,
        *,
        status: JobStatus | None = None,
        queue_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobModel]:
        stmt = select(JobModel)

        if status is not None:
            stmt = stmt.where(JobModel.status == status.value)

        if queue_name is not None:
            stmt = stmt.where(JobModel.queue_name == queue_name)

        stmt = (
            stmt.order_by(JobModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(self.db.execute(stmt).scalars().all())

    def claim_available_jobs(
        self,
        *,
        worker_id: str,
        worker_run_id: uuid.UUID,
        queues: list[str],
        batch_size: int,
        lock_timeout_seconds: int,
    ) -> list[JobModel]:
        """
        Claim available jobs safely for a worker.

        This uses SELECT ... FOR UPDATE SKIP LOCKED so multiple workers
        can claim jobs concurrently without claiming the same rows.
        """
        now = utc_now()

        claimable_statuses = [
            JobStatus.PENDING.value,
            JobStatus.RETRY_SCHEDULED.value,
        ]

        stmt: Select[tuple[JobModel]] = (
            select(JobModel)
            .where(JobModel.queue_name.in_(queues))
            .where(JobModel.status.in_(claimable_statuses))
            .where(JobModel.available_at <= now)
            .where(JobModel.attempt_count < JobModel.max_attempts)
            .order_by(
                JobModel.priority.desc(),
                JobModel.available_at.asc(),
                JobModel.created_at.asc(),
            )
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )

        jobs = list(self.db.execute(stmt).scalars().all())

        locked_until_expr = func.now() + (
            lock_timeout_seconds * text_interval_one_second()
        )

        for job in jobs:
            job.status = JobStatus.RUNNING.value
            job.locked_by = worker_id
            job.locked_by_run_id = worker_run_id
            job.locked_until = self._db_time_plus_seconds(lock_timeout_seconds)
            job.attempt_count += 1
            job.updated_at = now

        self.db.commit()

        for job in jobs:
            self.db.refresh(job)

        return jobs

    def renew_lock(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: str,
        worker_run_id: uuid.UUID,
        lock_timeout_seconds: int,
    ) -> bool:
        """
        Renew the lock for a running job.

        Returns True only if the current worker still owns the job.
        """
        new_locked_until = self._db_time_plus_seconds(lock_timeout_seconds)

        stmt = (
            update(JobModel)
            .where(JobModel.id == job_id)
            .where(JobModel.locked_by == worker_id)
            .where(JobModel.locked_by_run_id == worker_run_id)
            .where(JobModel.status == JobStatus.RUNNING.value)
            .values(
                locked_until=new_locked_until,
                updated_at=utc_now(),
            )
        )

        result = self.db.execute(stmt)
        self.db.commit()

        return result.rowcount == 1

    def mark_succeeded(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: str,
        worker_run_id: uuid.UUID,
    ) -> bool:
        now = utc_now()

        stmt = (
            update(JobModel)
            .where(JobModel.id == job_id)
            .where(JobModel.locked_by == worker_id)
            .where(JobModel.locked_by_run_id == worker_run_id)
            .where(JobModel.status == JobStatus.RUNNING.value)
            .values(
                status=JobStatus.SUCCEEDED.value,
                locked_by=None,
                locked_by_run_id=None,
                locked_until=None,
                completed_at=now,
                updated_at=now,
            )
        )

        result = self.db.execute(stmt)
        self.db.commit()

        return result.rowcount == 1

    def mark_retry_scheduled(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: str,
        worker_run_id: uuid.UUID,
        available_at: datetime,
        error_type: FailureType,
        error_message: str,
    ) -> bool:
        now = utc_now()

        stmt = (
            update(JobModel)
            .where(JobModel.id == job_id)
            .where(JobModel.locked_by == worker_id)
            .where(JobModel.locked_by_run_id == worker_run_id)
            .where(JobModel.status == JobStatus.RUNNING.value)
            .values(
                status=JobStatus.RETRY_SCHEDULED.value,
                locked_by=None,
                locked_by_run_id=None,
                locked_until=None,
                available_at=available_at,
                last_error_type=error_type.value,
                last_error_message=error_message,
                updated_at=now,
            )
        )

        result = self.db.execute(stmt)
        self.db.commit()

        return result.rowcount == 1

    def mark_dead_letter(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: str | None = None,
        worker_run_id: uuid.UUID | None = None,
        error_type: FailureType,
        error_message: str,
    ) -> bool:
        now = utc_now()

        stmt = (
            update(JobModel)
            .where(JobModel.id == job_id)
            .where(JobModel.status != JobStatus.SUCCEEDED.value)
            .where(JobModel.status != JobStatus.CANCELLED.value)
            .values(
                status=JobStatus.DEAD_LETTER.value,
                locked_by=None,
                locked_by_run_id=None,
                locked_until=None,
                last_error_type=error_type.value,
                last_error_message=error_message,
                completed_at=now,
                updated_at=now,
            )
        )

        if worker_id is not None:
            stmt = stmt.where(JobModel.locked_by == worker_id)

        if worker_run_id is not None:
            stmt = stmt.where(JobModel.locked_by_run_id == worker_run_id)

        result = self.db.execute(stmt)
        self.db.commit()

        return result.rowcount == 1

    def find_stale_running_jobs(
        self,
        *,
        limit: int = 100,
    ) -> list[JobModel]:
        now = utc_now()

        stmt = (
            select(JobModel)
            .where(JobModel.status == JobStatus.RUNNING.value)
            .where(JobModel.locked_until.is_not(None))
            .where(JobModel.locked_until < now)
            .order_by(JobModel.locked_until.asc())
            .limit(limit)
        )

        return list(self.db.execute(stmt).scalars().all())

    def reschedule_stale_job(
        self,
        *,
        job_id: uuid.UUID,
        available_at: datetime,
        error_message: str,
    ) -> bool:
        now = utc_now()

        stmt = (
            update(JobModel)
            .where(JobModel.id == job_id)
            .where(JobModel.status == JobStatus.RUNNING.value)
            .values(
                status=JobStatus.RETRY_SCHEDULED.value,
                locked_by=None,
                locked_by_run_id=None,
                locked_until=None,
                available_at=available_at,
                last_error_type=FailureType.STALE_LOCK.value,
                last_error_message=error_message,
                updated_at=now,
            )
        )

        result = self.db.execute(stmt)
        self.db.commit()

        return result.rowcount == 1

    def count_by_status(self) -> dict[str, int]:
        stmt = (
            select(JobModel.status, func.count(JobModel.id))
            .group_by(JobModel.status)
        )

        rows = self.db.execute(stmt).all()

        return {status: count for status, count in rows}

    @staticmethod
    def _db_time_plus_seconds(seconds: int) -> datetime:
        """
        For v1, calculate lock expiration in Python.

        This is simpler to read. In a stricter distributed setup, we could
        use database-side now() + interval arithmetic to avoid clock drift.
        """
        from datetime import timedelta

        return utc_now() + timedelta(seconds=seconds)