from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    RETRY_SCHEDULED = "retry_scheduled"
    SUCCEEDED = "succeeded"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class JobAttemptStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class JobType(StrEnum):
    SEND_EMAIL = "send_email"
    GENERATE_REPORT = "generate_report"
    SYNC_EXTERNAL_ACCOUNT = "sync_external_account"
    RUN_AI_ANALYSIS = "run_ai_analysis"


class FailureType(StrEnum):
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"
    AMBIGUOUS = "ambiguous"
    UNEXPECTED = "unexpected"
    STALE_LOCK = "stale_lock"


class ExecutionOutcomeStatus(StrEnum):
    SUCCESS = "success"
    RETRYABLE_FAILURE = "retryable_failure"
    NON_RETRYABLE_FAILURE = "non_retryable_failure"
    AMBIGUOUS_FAILURE = "ambiguous_failure"