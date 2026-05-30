from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_session
from app.api.schemas.jobs import (
    CreateJobRequest,
    JobAttemptResponse,
    JobResponse,
)
from app.application.commands.create_job import CreateJobCommand
from app.application.queries.job_queries import JobQueries
from app.application.services.job_service import JobService
from app.domain.jobs.enums import JobStatus
from app.infrastructure.repositories.job_attempt_repository import (
    JobAttemptRepository,
)
from app.infrastructure.repositories.job_repository import JobRepository


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    request: CreateJobRequest,
    session: Session = Depends(get_session),
) -> JobResponse:
    """
    Create a job.

    This endpoint only persists the job. It does not execute it.
    """
    job_repository = JobRepository(session)
    service = JobService(job_repository)

    command = CreateJobCommand(
        job_type=request.job_type,
        queue_name=request.queue_name,
        payload=request.payload,
        idempotency_key=request.idempotency_key,
        priority=request.priority,
        available_at=request.available_at,
        max_attempts=request.max_attempts,
    )

    job = service.create_job(command)
    session.commit()

    return JobResponse.from_domain(job)


@router.get(
    "",
    response_model=list[JobResponse],
)
def list_jobs(
    status_filter: JobStatus | None = Query(
        default=None,
        alias="status",
    ),
    queue_name: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[JobResponse]:
    """
    List jobs with optional filters.
    """
    job_repository = JobRepository(session)
    attempt_repository = JobAttemptRepository(session)
    queries = JobQueries(job_repository, attempt_repository)

    jobs = queries.list_jobs(
        status=status_filter,
        queue_name=queue_name,
        limit=limit,
        offset=offset,
    )

    return [JobResponse.from_domain(job) for job in jobs]


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: UUID,
    session: Session = Depends(get_session),
) -> JobResponse:
    """
    Get a job by id.
    """
    job_repository = JobRepository(session)
    attempt_repository = JobAttemptRepository(session)
    queries = JobQueries(job_repository, attempt_repository)

    job = queries.get_job(job_id)

    return JobResponse.from_domain(job)


@router.get(
    "/{job_id}/attempts",
    response_model=list[JobAttemptResponse],
)
def list_job_attempts(
    job_id: UUID,
    session: Session = Depends(get_session),
) -> list[JobAttemptResponse]:
    """
    List attempts for a job.
    """
    job_repository = JobRepository(session)
    attempt_repository = JobAttemptRepository(session)
    queries = JobQueries(job_repository, attempt_repository)

    attempts = queries.list_attempts(job_id)

    return [JobAttemptResponse.from_domain(attempt) for attempt in attempts]