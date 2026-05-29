from app.domain.jobs.enums import FailureType


class JobExecutionError(Exception):
    """
    Base class for controlled job execution errors.

    These errors represent expected execution failures that the worker
    can classify and handle safely.
    """

    failure_type: FailureType = FailureType.UNEXPECTED

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RetryableJobError(JobExecutionError):
    """
    Temporary failure. The job may succeed if retried later.

    Examples:
    - provider unavailable
    - rate limit
    - network timeout before external side effect
    """

    failure_type = FailureType.RETRYABLE


class NonRetryableJobError(JobExecutionError):
    """
    Permanent failure. Retrying is not expected to help.

    Examples:
    - invalid payload
    - missing required field
    - invalid recipient
    - bad credentials
    """

    failure_type = FailureType.NON_RETRYABLE


class AmbiguousJobError(JobExecutionError):
    """
    Ambiguous failure. The external side effect may or may not have happened.

    Examples:
    - timeout after request was sent
    - connection dropped after provider may have accepted the request
    - worker crash after external success
    """

    failure_type = FailureType.AMBIGUOUS


class JobLockLostError(JobExecutionError):
    """
    The worker no longer owns the job lock.

    This should prevent the worker from finalizing the job.
    """

    failure_type = FailureType.STALE_LOCK