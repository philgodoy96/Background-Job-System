from uuid import UUID

from app.core.errors import NotFoundError
from app.domain.jobs.entities import Job, JobAttempt
from app.domain.jobs.enums import JobStatus
from app.infrastructure.repositories.job_attempt_repository import (
    JobAttemptRepository,
)
from app.infrastructure.repositories.job_repository import JobRepository


class JobQueries:
    """
    Application query service for jobs and job attempts.
    """

    def __init__(
        self,
        job_repository: JobRepository,
        job_attempt_repository: JobAttemptRepository,
    ) -> None:
        self.job_repository = job_repository
        self.job_attempt_repository = job_attempt_repository

    def get_job(self, job_id: UUID) -> Job:
        """
        Return a job by id or raise NotFoundError.
        """
        job = self.job_repository.get_by_id(job_id)

        if job is None:
            raise NotFoundError(
                "Job not found",
                code="JOB_NOT_FOUND",
            )

        return job

    def list_jobs(
        self,
        *,
        status: JobStatus | None,
        queue_name: str | None,
        limit: int,
        offset: int,
    ) -> list[Job]:
        """
        List jobs with optional filters.
        """
        return self.job_repository.list_jobs(
            status=status,
            queue_name=queue_name,
            limit=limit,
            offset=offset,
        )

    def list_attempts(self, job_id: UUID) -> list[JobAttempt]:
        """
        List attempts for a job.

        We first check that the job exists so the API can return 404 for an
        unknown job instead of returning an empty attempts list.
        """
        self.get_job(job_id)

        return self.job_attempt_repository.list_by_job_id(job_id)