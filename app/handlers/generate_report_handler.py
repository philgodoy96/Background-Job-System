from app.domain.jobs.entities import Job
from app.domain.jobs.errors import NonRetryableJobError, RetryableJobError
from app.handlers.base import HandlerResult
from app.providers.fake_report_provider import (
    FakeInvalidReportRequestError,
    FakeReportProvider,
    FakeReportTemporaryFailureError,
)


class GenerateReportHandler:
    """
    Handler for generate_report jobs.
    """

    def __init__(self, *, report_provider: FakeReportProvider) -> None:
        self.report_provider = report_provider

    def handle(self, job: Job) -> HandlerResult:
        """
        Execute a generate_report job.

        Expected payload:
        {
            "report_ref": "report_123",
            "simulation": "success | slow_success | temporary_failure | invalid_request"
        }
        """
        payload = job.payload

        report_ref = payload.get("report_ref")
        simulation = payload.get("simulation")

        if not report_ref:
            raise NonRetryableJobError(
                "generate_report payload requires report_ref",
                code="MISSING_REPORT_REF",
            )

        try:
            result = self.report_provider.generate_report(
                report_ref=report_ref,
                simulation=simulation,
            )
        except FakeReportTemporaryFailureError as exc:
            raise RetryableJobError(
                str(exc),
                code="REPORT_TEMPORARY_FAILURE",
            ) from exc
        except FakeInvalidReportRequestError as exc:
            raise NonRetryableJobError(
                str(exc),
                code="INVALID_REPORT_REQUEST",
            ) from exc

        return HandlerResult(
            message="Report generated successfully",
            metadata={
                "report_id": result.report_id,
                "storage_uri": result.storage_uri,
            },
        )