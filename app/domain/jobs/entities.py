from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.jobs.enums import AttemptStatus, JobStatus, JobType


@dataclass(slots=True)
class Job:
    """
    Domain representation of a background job.

    A job represents one unit of asynchronous work.
    """

    id: UUID
    type: JobType
    queue_name: str
    status: JobStatus
    payload: dict
    idempotency_key: str | None
    priority: int
    available_at: datetime
    attempt_count: int
    max_attempts: int
    locked_by: str | None
    locked_by_run_id: str | None
    locked_until: datetime | None
    last_error_type: str | None
    last_error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            JobStatus.SUCCEEDED,
            JobStatus.DEAD_LETTER,
            JobStatus.CANCELLED,
        }

    @property
    def can_be_claimed(self) -> bool:
        return self.status in {
            JobStatus.PENDING,
            JobStatus.RETRY_SCHEDULED,
        }

    @property
    def attempts_remaining(self) -> int:
        return max(self.max_attempts - self.attempt_count, 0)

    @property
    def has_attempts_remaining(self) -> bool:
        return self.attempt_count < self.max_attempts


@dataclass(slots=True)
class JobAttempt:
    """
    Domain representation of one execution attempt for a job.

    One job may have multiple attempts.
    """

    id: UUID
    job_id: UUID
    attempt_number: int
    worker_id: str
    worker_run_id: str
    status: AttemptStatus
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    error_type: str | None
    error_message: str | None
    created_at: datetime