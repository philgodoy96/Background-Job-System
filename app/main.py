from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging, get_logger


configure_logging()

logger = get_logger(__name__)
settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.exception_handler(AppError)
async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    """
    Convert expected application errors into structured HTTP responses.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            }
        },
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Basic health endpoint.

    This only proves that the API process is running.
    It does not prove that the database or workers are healthy.
    """
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }