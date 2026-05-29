from dataclasses import dataclass

from app.domain.jobs.enums import ExecutionOutcomeStatus, JobStatus
from app.domain.jobs.entities import ExecutionOutcome, Job


TERMINAL_STATUSES = {
    JobStatus.SUCCEEDED,
    JobStatus.DEAD_LETTER,
    JobStatus.CANCELLED,
}

CLAIMABLE_STATUSES = {
    JobStatus.PENDING,
    JobStatus.RETRY_SCHEDULED,
}


@dataclass(frozen=True)
class JobFailureDecision:
    next_status: JobStatus
    should_retry: bool
    should_dead_letter: bool


def is_terminal_status(status: JobStatus) -> bool:
    return status in TERMINAL_STATUSES


def is_claimable_status(status: JobStatus) -> bool:
    return status in CLAIMABLE_STATUSES


def has_attempts_remaining(job: Job) -> bool:
    return job.attempt_count < job.max_attempts


def next_attempt_number(job: Job) -> int:
    return job.attempt_count + 1


def decide_failure_transition(
    job: Job,
    outcome: ExecutionOutcome,
) -> JobFailureDecision:
    """
    Decide what should happen to a job after a failed execution outcome.

    This function does not persist anything.
    It only makes the lifecycle decision explicit and testable.
    """
    if outcome.status == ExecutionOutcomeStatus.NON_RETRYABLE_FAILURE:
        return JobFailureDecision(
            next_status=JobStatus.DEAD_LETTER,
            should_retry=False,
            should_dead_letter=True,
        )

    if outcome.status in {
        ExecutionOutcomeStatus.RETRYABLE_FAILURE,
        ExecutionOutcomeStatus.AMBIGUOUS_FAILURE,
    }:
        if has_attempts_remaining(job):
            return JobFailureDecision(
                next_status=JobStatus.RETRY_SCHEDULED,
                should_retry=True,
                should_dead_letter=False,
            )

        return JobFailureDecision(
            next_status=JobStatus.DEAD_LETTER,
            should_retry=False,
            should_dead_letter=True,
        )

    raise ValueError(
        f"Cannot decide failure transition for outcome status: {outcome.status}"
    )


def ensure_can_finalize(job: Job) -> None:
    """
    Guard against finalizing terminal jobs accidentally.
    """
    if is_terminal_status(job.status):
        raise ValueError(f"Cannot finalize terminal job with status {job.status}")


def ensure_can_claim(job: Job) -> None:
    """
    Guard against claiming jobs that are not claimable.
    """
    if not is_claimable_status(job.status):
        raise ValueError(f"Cannot claim job with status {job.status}")