from dataclasses import dataclass
from uuid import uuid4


class FakeRateLimitedError(Exception):
    """
    Raised when the external account provider rate limits the request.
    """


class FakeBadCredentialsError(Exception):
    """
    Raised when the external account credentials are invalid.
    """


@dataclass(frozen=True, slots=True)
class FakeExternalAccountSyncResult:
    sync_id: str
    external_account_ref: str


class FakeExternalAccountProvider:
    """
    Fake provider used to simulate syncing an external account.
    """

    def sync_account(
        self,
        *,
        external_account_ref: str,
        simulation: str | None = None,
    ) -> FakeExternalAccountSyncResult:
        """
        Sync an external account.
        """
        if simulation == "rate_limited":
            raise FakeRateLimitedError(
                "External account provider rate limited the request"
            )

        if simulation == "bad_credentials":
            raise FakeBadCredentialsError(
                "External account credentials are invalid"
            )

        return FakeExternalAccountSyncResult(
            sync_id=f"fake-sync-{uuid4()}",
            external_account_ref=external_account_ref,
        )