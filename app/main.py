import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import jobs, metrics
from app.core.config import get_settings
from app.core.errors import AppError, ConflictError, NotFoundError, ValidationError
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


@app.exception_handler(AppError)
def handle_app_error(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    """
    Translate application errors into HTTP responses.
    """
    status_code = 500

    if isinstance(exc, ValidationError):
        status_code = 400
    elif isinstance(exc, NotFoundError):
        status_code = 404
    elif isinstance(exc, ConflictError):
        status_code = 409

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
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


app.include_router(jobs.router)
app.include_router(metrics.router)