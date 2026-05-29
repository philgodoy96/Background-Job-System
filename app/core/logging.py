import logging

from app.core.config import get_settings


def configure_logging() -> None:
    """
    Configure application-wide logging.

    This is intentionally simple for v1.
    Later, this can evolve to JSON logs or OpenTelemetry integration.
    """
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.
    """
    return logging.getLogger(name)