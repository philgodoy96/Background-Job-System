from enum import StrEnum


class JobStatus(StrEnum):
    """
    Lifecycle status of a job.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    SUCCEEDED = "SUCCEEDED"
    DEAD_LETTER = "DEAD_LETTER"
    CANCELLED = "CANCELLED"


class AttemptStatus(StrEnum):
    """
    Lifecycle status of a single job execution attempt.
    """

    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"


class JobType(StrEnum):
    """
    Supported job types for v1.
    """

    SEND_EMAIL = "send_email"
    GENERATE_REPORT = "generate_report"
    SYNC_EXTERNAL_ACCOUNT = "sync_external_account"
    RUN_AI_ANALYSIS = "run_ai_analysis"