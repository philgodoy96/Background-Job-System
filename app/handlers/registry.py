from app.domain.jobs.enums import JobType
from app.domain.jobs.errors import NonRetryableJobError
from app.handlers.base import JobHandler
from app.handlers.generate_report_handler import GenerateReportHandler
from app.handlers.run_ai_analysis_handler import RunAIAnalysisHandler
from app.handlers.send_email_handler import SendEmailHandler
from app.handlers.sync_external_account_handler import SyncExternalAccountHandler
from app.infrastructure.repositories.email_delivery_repository import (
    EmailDeliveryRepository,
)
from app.providers.fake_ai_provider import FakeAIProvider
from app.providers.fake_email_provider import FakeEmailProvider
from app.providers.fake_external_account_provider import FakeExternalAccountProvider
from app.providers.fake_report_provider import FakeReportProvider


class HandlerRegistry:
    """
    Registry that maps job types to handlers.
    """

    def __init__(
        self,
        *,
        email_delivery_repository: EmailDeliveryRepository,
    ) -> None:
        self._handlers: dict[JobType, JobHandler] = {
            JobType.SEND_EMAIL: SendEmailHandler(
                email_delivery_repository=email_delivery_repository,
                email_provider=FakeEmailProvider(),
            ),
            JobType.GENERATE_REPORT: GenerateReportHandler(
                report_provider=FakeReportProvider(),
            ),
            JobType.SYNC_EXTERNAL_ACCOUNT: SyncExternalAccountHandler(
                external_account_provider=FakeExternalAccountProvider(),
            ),
            JobType.RUN_AI_ANALYSIS: RunAIAnalysisHandler(
                ai_provider=FakeAIProvider(),
            ),
        }

    def get(self, job_type: JobType) -> JobHandler:
        """
        Return a handler for a job type.
        """
        handler = self._handlers.get(job_type)

        if handler is None:
            raise NonRetryableJobError(
                f"No handler registered for job type: {job_type}",
                code="HANDLER_NOT_FOUND",
            )

        return handler