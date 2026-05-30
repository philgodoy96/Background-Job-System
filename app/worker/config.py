from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class WorkerConfig:
    """
    Runtime configuration for a worker process.
    """

    queue_name: str
    batch_size: int
    poll_interval_seconds: int
    lock_timeout_seconds: int
    max_execution_seconds: int


def build_worker_config(queue_name: str = "default") -> WorkerConfig:
    """
    Build worker configuration from application settings.
    """
    settings = get_settings()

    return WorkerConfig(
        queue_name=queue_name,
        batch_size=settings.worker_batch_size,
        poll_interval_seconds=settings.worker_poll_interval_seconds,
        lock_timeout_seconds=settings.lock_timeout_seconds,
        max_execution_seconds=settings.max_execution_seconds,
    )