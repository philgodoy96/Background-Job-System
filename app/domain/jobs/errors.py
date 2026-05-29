from app.core.errors import AppError


class JobError(AppError):
    """
    Base class for job-related errors.
    """


class RetryableJobError(JobError):
    """
    Raised when a job failure may succeed if retried later.

    Examples:
    - provider unavailable
    - rate limit
    - temporary network error
    - AI timeout
    - invalid LLM output when retry may fix it
    """


class NonRetryableJobError(JobError):
    """
    Raised when retrying the job will not fix the problem.

    Examples:
    - invalid payload
    - missing required field
    - invalid recipient
    - bad credentials
    - rejected request
    """


class AmbiguousJobError(JobError):
    """
    Raised when the worker cannot know if an external side effect happened.

    Example:
    The request reached the provider, but the worker timed out before receiving
    confirmation.

    These cases must be handled carefully to avoid duplicate side effects.
    """


class LockLostError(JobError):
    """
    Raised when a worker no longer owns the job lock.

    If a worker loses ownership, it must not mark the job as succeeded.
    """


class JobTimeoutError(JobError):
    """
    Raised when a job exceeds the maximum allowed execution time.
    """


class InvalidJobTransitionError(JobError):
    """
    Raised when a job status transition is not allowed.
    """