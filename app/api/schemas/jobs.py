from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.jobs.entities import Job, JobAttempt
from app.domain.jobs.enums import AttemptStatus, JobStatus, JobType


class CreateJobRequest(BaseModel):
    """
    Request body for POST /jobs.
    """

    job_type: JobType = Field(
        ...,
        description="Type of job to create.",
    )
    queue_name: str = Field(
        default="default",
        min_length=1,
        max_length=100,
        description="Queue where the job should be processed.",
    )
    payload: dict = Field(
        default_factory=dict,
        description="Job payload. Avoid sending secrets or unnecessary PII.",
    )
    idempotency_key: str | None = Field(
        default=None,
        max_length=255,
        description="Business idempotency key for safe retries.",
    )
    priority: int = Field(
        default=0,
        ge=0,
        description="Higher priority jobs are claimed first.",
    )
    available_at: datetime | None = Field(
        default=None,
        description="When this job becomes eligible for processing.",
    )
    max_attempts: int | None = Field(
        default=None,
        ge=1,
        description="Maximum number of execution attempts.",
    )


class JobResponse(BaseModel):
    """
    API response representation of a job.
    """

    id: UUID
    job_type: JobType
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

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, job: Job) -> "JobResponse":
        return cls(
            id=job.id,
            job_type=job.type,
            queue_name=job.queue_name,
            status=job.status,
            payload=job.payload,
            idempotency_key=job.idempotency_key,
            priority=job.priority,
            available_at=job.available_at,
            attempt_count=job.attempt_count,
            max_attempts=job.max_attempts,
            locked_by=job.locked_by,
            locked_by_run_id=job.locked_by_run_id,
            locked_until=job.locked_until,
            last_error_type=job.last_error_type,
            last_error_message=job.last_error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
        )


class JobAttemptResponse(BaseModel):
    """
    API response representation of a job attempt.
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

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, attempt: JobAttempt) -> "JobAttemptResponse":
        return cls(
            id=attempt.id,
            job_id=attempt.job_id,
            attempt_number=attempt.attempt_number,
            worker_id=attempt.worker_id,
            worker_run_id=attempt.worker_run_id,
            status=attempt.status,
            started_at=attempt.started_at,
            finished_at=attempt.finished_at,
            duration_ms=attempt.duration_ms,
            error_type=attempt.error_type,
            error_message=attempt.error_message,
            created_at=attempt.created_at,
        )