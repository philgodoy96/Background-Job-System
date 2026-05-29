from app.domain.jobs.enums import JobStatus
from app.domain.jobs.errors import InvalidJobTransitionError


_ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.PENDING: {
        JobStatus.RUNNING,
        JobStatus.CANCELLED,
    },
    JobStatus.RETRY_SCHEDULED: {
        JobStatus.RUNNING,
        JobStatus.CANCELLED,
    },
    JobStatus.RUNNING: {
        JobStatus.SUCCEEDED,
        JobStatus.RETRY_SCHEDULED,
        JobStatus.DEAD_LETTER,
    },
    JobStatus.SUCCEEDED: set(),
    JobStatus.DEAD_LETTER: set(),
    JobStatus.CANCELLED: set(),
}


def can_transition(from_status: JobStatus, to_status: JobStatus) -> bool:
    """
    Return True if a job may transition from one status to another.
    """
    return to_status in _ALLOWED_TRANSITIONS[from_status]


def ensure_can_transition(from_status: JobStatus, to_status: JobStatus) -> None:
    """
    Raise an error if a job status transition is not allowed.
    """
    if not can_transition(from_status, to_status):
        raise InvalidJobTransitionError(
            f"Invalid job status transition: {from_status} -> {to_status}",
            code="INVALID_JOB_STATUS_TRANSITION",
        )


def is_terminal_status(status: JobStatus) -> bool:
    """
    Return True if the job status is terminal.
    """
    return status in {
        JobStatus.SUCCEEDED,
        JobStatus.DEAD_LETTER,
        JobStatus.CANCELLED,
    }


def is_claimable_status(status: JobStatus) -> bool:
    """
    Return True if a job with this status can be claimed by a worker.
    """
    return status in {
        JobStatus.PENDING,
        JobStatus.RETRY_SCHEDULED,
    }