class LogEvent:
    """
    Centralized log event names.

    Keeping event names here helps avoid typos and makes logs easier to query.
    """

    APP_STARTED = "app_started"
    HEALTH_CHECK_CALLED = "health_check_called"

    WORKER_STARTED = "worker_started"
    WORKER_STOPPED = "worker_stopped"

    JOB_CREATED = "job_created"
    JOB_CLAIMED = "job_claimed"
    JOB_ATTEMPT_STARTED = "job_attempt_started"
    JOB_SUCCEEDED = "job_succeeded"
    JOB_FAILED = "job_failed"
    JOB_RETRY_SCHEDULED = "job_retry_scheduled"
    JOB_DEAD_LETTERED = "job_dead_lettered"

    HEARTBEAT_RENEWED = "heartbeat_renewed"
    HEARTBEAT_LOST = "heartbeat_lost"
    HEARTBEAT_STOPPED = "heartbeat_stopped"

    STALE_JOB_FOUND = "stale_job_found"
    STALE_JOB_RECOVERED = "stale_job_recovered"

    EMAIL_DELIVERY_CREATED = "email_delivery_created"
    EMAIL_DELIVERY_ALREADY_SENT = "email_delivery_already_sent"
    EMAIL_DELIVERY_SENT = "email_delivery_sent"
    EMAIL_DELIVERY_UNKNOWN = "email_delivery_unknown"