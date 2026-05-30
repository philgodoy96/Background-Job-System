import time
from dataclasses import dataclass
from uuid import uuid4


class FakeEmailProviderUnavailableError(Exception):
    """
    Raised when the fake email provider is temporarily unavailable.
    """


class FakeInvalidRecipientError(Exception):
    """
    Raised when the fake email provider rejects the recipient.
    """


class FakeEmailAmbiguousTimeoutError(Exception):
    """
    Raised when the provider may have received the request but no confirmation
    was returned.
    """


@dataclass(frozen=True, slots=True)
class FakeEmailProviderResult:
    provider_message_id: str


class FakeEmailProvider:
    """
    Fake email provider used to simulate external provider behavior.

    The behavior is controlled by payload["simulation"].
    """

    def send_email(
        self,
        *,
        recipient: str,
        template: str,
        idempotency_key: str,
        simulation: str | None = None,
    ) -> FakeEmailProviderResult:
        """
        Send an email using a fake provider.
        """
        if simulation == "provider_unavailable":
            raise FakeEmailProviderUnavailableError(
                "Email provider is temporarily unavailable"
            )

        if simulation == "invalid_recipient":
            raise FakeInvalidRecipientError(
                "Recipient is invalid"
            )

        if simulation == "ambiguous_timeout":
            raise FakeEmailAmbiguousTimeoutError(
                "Email provider request timed out after being sent"
            )

        if simulation == "slow_success":
            time.sleep(5)

        return FakeEmailProviderResult(
            provider_message_id=f"fake-email-{uuid4()}",
        )