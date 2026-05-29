from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.jobs.enums import (
    ExecutionOutcomeStatus,
    FailureType,
    JobAttemptStatus,
    JobStatus,
    JobType,
)


@dataclass
class Job:
    id: UUID
    type: JobType
    queue_name: str
    status: JobStatus
    payload: dict[str, Any]
    idempotency_key: str | None
    priority: int
    available_at: datetime
    attempt_count: int
    max_attempts: int
    locked_by: str | None
    locked_by_run_id: UUID | None
    locked_until: datetime | None
    last_error_type: FailureType | None
    last_error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


@dataclass
class JobAttempt:
    id: UUID
    job_id: UUID
    attempt_number: int
    worker_id: str
    worker_run_id: UUID
    status: JobAttemptStatus
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    error_type: FailureType | None
    error_message: str | None
    created_at: datetime


@dataclass(frozen=True)
class ExecutionOutcome:
    status: ExecutionOutcomeStatus
    message: str | None = None
    result: dict[str, Any] | None = None
    error_type: FailureType | None = None
    error_message: str | None = None

    @classmethod
    def success(
        cls,
        result: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> "ExecutionOutcome":
        return cls(
            status=ExecutionOutcomeStatus.SUCCESS,
            result=result,
            message=message,
        )

    @classmethod
    def retryable_failure(
        cls,
        message: str,
    ) -> "ExecutionOutcome":
        return cls(
            status=ExecutionOutcomeStatus.RETRYABLE_FAILURE,
            error_type=FailureType.RETRYABLE,
            error_message=message,
        )

    @classmethod
    def non_retryable_failure(
        cls,
        message: str,
    ) -> "ExecutionOutcome":
        return cls(
            status=ExecutionOutcomeStatus.NON_RETRYABLE_FAILURE,
            error_type=FailureType.NON_RETRYABLE,
            error_message=message,
        )

    @classmethod
    def ambiguous_failure(
        cls,
        message: str,
    ) -> "ExecutionOutcome":
        return cls(
            status=ExecutionOutcomeStatus.AMBIGUOUS_FAILURE,
            error_type=FailureType.AMBIGUOUS,
            error_message=message,
        )