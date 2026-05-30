from dataclasses import dataclass
from typing import Protocol

from app.domain.jobs.entities import Job


@dataclass(frozen=True, slots=True)
class HandlerResult:
    """
    Result returned by a job handler after successful execution.

    Handlers should raise job domain errors for failure cases.
    """

    message: str
    metadata: dict | None = None


class JobHandler(Protocol):
    """
    Protocol implemented by all job handlers.
    """

    def handle(self, job: Job) -> HandlerResult:
        """
        Execute a job.

        Implementations should return HandlerResult on success and raise
        RetryableJobError, NonRetryableJobError, or AmbiguousJobError on failure.
        """