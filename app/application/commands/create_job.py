from dataclasses import dataclass
from datetime import datetime

from app.domain.jobs.enums import JobType


@dataclass(frozen=True, slots=True)
class CreateJobCommand:
    """
    Application command used to create a job.

    Commands represent use-case input after API validation.
    """

    job_type: JobType
    queue_name: str
    payload: dict
    idempotency_key: str | None
    priority: int
    available_at: datetime | None
    max_attempts: int | None