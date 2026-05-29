from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application settings.

    Values can be overridden using environment variables or a local .env file.
    """

    app_name: str = "job-processing-system"
    environment: str = "local"
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/jobs_db"
    )

    default_job_max_attempts: int = 3

    worker_batch_size: int = 5
    worker_poll_interval_seconds: int = 2

    lock_timeout_seconds: int = 60
    heartbeat_interval_seconds: int = 20
    max_execution_seconds: int = 300

    retry_base_delay_seconds: int = 2
    retry_max_delay_seconds: int = 60
    retry_jitter_ratio: float = 0.2

    stale_recovery_batch_size: int = 20
    stale_recovery_poll_interval_seconds: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    This avoids rebuilding the settings object every time it is requested.
    """
    return Settings()