from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_session
from app.api.schemas.metrics import JobsSummaryResponse
from app.application.queries.metrics_queries import MetricsQueries


router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
)


@router.get(
    "/jobs-summary",
    response_model=JobsSummaryResponse,
)
def get_jobs_summary(
    session: Session = Depends(get_session),
) -> JobsSummaryResponse:
    """
    Return a simple count of jobs grouped by status.
    """
    queries = MetricsQueries(session)
    summary = queries.get_jobs_summary()

    return JobsSummaryResponse(**summary)