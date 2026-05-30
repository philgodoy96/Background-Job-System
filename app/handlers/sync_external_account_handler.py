from app.domain.jobs.entities import Job
from app.domain.jobs.errors import NonRetryableJobError, RetryableJobError
from app.handlers.base import HandlerResult
from app.providers.fake_external_account_provider import (
    FakeBadCredentialsError,
    FakeExternalAccountProvider,
    FakeRateLimitedError,
)


class SyncExternalAccountHandler:
    """
    Handler for sync_external_account jobs.
    """

    def __init__(
        self,
        *,
        external_account_provider: FakeExternalAccountProvider,
    ) -> None:
        self.external_account_provider = external_account_provider

    def handle(self, job: Job) -> HandlerResult:
        """
        Execute a sync_external_account job.

        Expected payload:
        {
            "external_account_ref": "acct_123",
            "simulation": "success | rate_limited | bad_credentials"
        }
        """
        payload = job.payload

        external_account_ref = payload.get("external_account_ref")
        simulation = payload.get("simulation")

        if not external_account_ref:
            raise NonRetryableJobError(
                "sync_external_account payload requires external_account_ref",
                code="MISSING_EXTERNAL_ACCOUNT_REF",
            )

        try:
            result = self.external_account_provider.sync_account(
                external_account_ref=external_account_ref,
                simulation=simulation,
            )
        except FakeRateLimitedError as exc:
            raise RetryableJobError(
                str(exc),
                code="EXTERNAL_ACCOUNT_RATE_LIMITED",
            ) from exc
        except FakeBadCredentialsError as exc:
            raise NonRetryableJobError(
                str(exc),
                code="EXTERNAL_ACCOUNT_BAD_CREDENTIALS",
            ) from exc

        return HandlerResult(
            message="External account synced successfully",
            metadata={
                "sync_id": result.sync_id,
                "external_account_ref": result.external_account_ref,
            },
        )