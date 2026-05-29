from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    These settings are shared by the API, workers, repositories,
    and background processing components.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Job Processing System"
    environment: str = "development"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/jobs_db"

    default_queue_name: str = "default"
    default_max_attempts: int = 3

    worker_batch_size: int = 5
    worker_poll_interval_seconds: int = 2

    worker_lock_timeout_seconds: int = 60

    heartbeat_enabled: bool = True
    heartbeat_interval_seconds: int = 20
    max_execution_seconds: int = 300

    retry_base_delay_seconds: int = 5
    retry_jitter_ratio: float = 0.2
    retry_max_delay_seconds: int = 300

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """
    Return cached application settings.

    Using lru_cache avoids re-reading environment variables repeatedly.
    """
    return Settings()