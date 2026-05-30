import time
from dataclasses import dataclass
from uuid import uuid4


class FakeReportTemporaryFailureError(Exception):
    """
    Raised when report generation fails temporarily.
    """


class FakeInvalidReportRequestError(Exception):
    """
    Raised when the report request is invalid.
    """


@dataclass(frozen=True, slots=True)
class FakeReportProviderResult:
    report_id: str
    storage_uri: str


class FakeReportProvider:
    """
    Fake report provider used to simulate report generation.
    """

    def generate_report(
        self,
        *,
        report_ref: str,
        simulation: str | None = None,
    ) -> FakeReportProviderResult:
        """
        Generate a fake report.
        """
        if simulation == "temporary_failure":
            raise FakeReportTemporaryFailureError(
                "Report generation temporarily failed"
            )

        if simulation == "invalid_request":
            raise FakeInvalidReportRequestError(
                "Report request is invalid"
            )

        if simulation == "slow_success":
            time.sleep(10)

        return FakeReportProviderResult(
            report_id=f"fake-report-{uuid4()}",
            storage_uri=f"s3://fake-bucket/reports/{report_ref}.pdf",
        )