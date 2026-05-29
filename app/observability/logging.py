import logging
import sys
from typing import Any

from app.core.config import get_settings


def configure_logging() -> None:
    """
    Configure application logging.

    This is intentionally simple for v1. Later, we can replace the format with
    JSON logs without changing every caller.
    """
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger for a given module.
    """
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    **fields: Any,
) -> None:
    """
    Log an event with structured context.

    For v1, fields are appended as key-value pairs in the message.

    Avoid passing raw payloads, secrets, tokens, full emails, CPF, or any
    sensitive personal data.
    """
    if fields:
        field_text = " ".join(f"{key}={value}" for key, value in fields.items())
        logger.log(level, "%s %s", event, field_text)
        return

    logger.log(level, "%s", event)