from app.application.commands.create_job import CreateJobCommand
from app.core.config import get_settings
from app.core.errors import ValidationError
from app.domain.jobs.entities import Job
from app.infrastructure.repositories.job_repository import JobRepository


class JobService:
    """
    Application service for job write use cases.
    """

    def __init__(self, job_repository: JobRepository) -> None:
        self.job_repository = job_repository
        self.settings = get_settings()

    def create_job(self, command: CreateJobCommand) -> Job:
        """
        Create a new job.

        The API creates the job but does not execute it.
        Workers will pick it up later.
        """
        queue_name = command.queue_name.strip()

        if not queue_name:
            raise ValidationError(
                "queue_name cannot be empty",
                code="EMPTY_QUEUE_NAME",
            )

        if command.priority < 0:
            raise ValidationError(
                "priority cannot be negative",
                code="INVALID_PRIORITY",
            )

        max_attempts = command.max_attempts or self.settings.default_job_max_attempts

        if max_attempts <= 0:
            raise ValidationError(
                "max_attempts must be greater than zero",
                code="INVALID_MAX_ATTEMPTS",
            )

        return self.job_repository.create_job(
            job_type=command.job_type,
            queue_name=queue_name,
            payload=command.payload,
            idempotency_key=command.idempotency_key,
            priority=command.priority,
            available_at=command.available_at,
            max_attempts=max_attempts,
        )