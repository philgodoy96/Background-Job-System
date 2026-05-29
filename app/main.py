import logging

from fastapi import FastAPI

from app.core.config import get_settings
from app.observability.events import LogEvent
from app.observability.logging import configure_logging, get_logger, log_event


configure_logging()

settings = get_settings()
logger = get_logger(__name__)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    """
    Application startup hook.
    """
    log_event(
        logger,
        logging.INFO,
        LogEvent.APP_STARTED,
        service=settings.app_name,
        environment=settings.environment,
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    This endpoint verifies that the API process is running.
    It does not check database connectivity yet.
    """
    log_event(
        logger,
        logging.INFO,
        LogEvent.HEALTH_CHECK_CALLED,
        service=settings.app_name,
    )

    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }