from app.domain.jobs.entities import Job
from app.domain.jobs.errors import (
    AmbiguousJobError,
    NonRetryableJobError,
    RetryableJobError,
)
from app.domain.side_effects.enums import EmailDeliveryStatus
from app.handlers.base import HandlerResult
from app.infrastructure.repositories.email_delivery_repository import (
    EmailDeliveryRepository,
)
from app.providers.fake_email_provider import (
    FakeEmailAmbiguousTimeoutError,
    FakeEmailProvider,
    FakeEmailProviderUnavailableError,
    FakeInvalidRecipientError,
)


class SendEmailHandler:
    """
    Handler for send_email jobs.

    This handler demonstrates local idempotency using EmailDelivery.
    """

    def __init__(
        self,
        *,
        email_delivery_repository: EmailDeliveryRepository,
        email_provider: FakeEmailProvider,
    ) -> None:
        self.email_delivery_repository = email_delivery_repository
        self.email_provider = email_provider

    def handle(self, job: Job) -> HandlerResult:
        """
        Execute a send_email job.

        Expected payload:
        {
            "recipient_ref": "user_123",
            "template": "welcome",
            "simulation": "success | provider_unavailable | invalid_recipient | ambiguous_timeout | slow_success"
        }
        """
        payload = job.payload

        recipient_ref = payload.get("recipient_ref")
        template = payload.get("template")
        simulation = payload.get("simulation")

        if not recipient_ref:
            raise NonRetryableJobError(
                "send_email payload requires recipient_ref",
                code="MISSING_RECIPIENT_REF",
            )

        if not template:
            raise NonRetryableJobError(
                "send_email payload requires template",
                code="MISSING_TEMPLATE",
            )

        if job.idempotency_key is None:
            raise NonRetryableJobError(
                "send_email job requires idempotency_key",
                code="MISSING_IDEMPOTENCY_KEY",
            )

        delivery = self.email_delivery_repository.get_or_create(
            idempotency_key=job.idempotency_key,
            recipient=recipient_ref,
            template=template,
        )

        if delivery.status == EmailDeliveryStatus.SENT:
            return HandlerResult(
                message="Email delivery already sent; skipped provider call",
                metadata={
                    "email_delivery_id": str(delivery.id),
                    "idempotent_skip": True,
                },
            )

        if delivery.status == EmailDeliveryStatus.UNKNOWN:
            raise AmbiguousJobError(
                "Email delivery is UNKNOWN; reconciliation is required before safe retry",
                code="EMAIL_DELIVERY_UNKNOWN",
            )

        try:
            result = self.email_provider.send_email(
                recipient=recipient_ref,
                template=template,
                idempotency_key=job.idempotency_key,
                simulation=simulation,
            )
        except FakeEmailProviderUnavailableError as exc:
            raise RetryableJobError(
                str(exc),
                code="EMAIL_PROVIDER_UNAVAILABLE",
            ) from exc
        except FakeInvalidRecipientError as exc:
            self.email_delivery_repository.mark_failed(delivery_id=delivery.id)
            raise NonRetryableJobError(
                str(exc),
                code="INVALID_RECIPIENT",
            ) from exc
        except FakeEmailAmbiguousTimeoutError as exc:
            self.email_delivery_repository.mark_unknown(delivery_id=delivery.id)
            raise AmbiguousJobError(
                str(exc),
                code="EMAIL_AMBIGUOUS_TIMEOUT",
            ) from exc

        self.email_delivery_repository.mark_sent(
            delivery_id=delivery.id,
            provider_message_id=result.provider_message_id,
        )

        return HandlerResult(
            message="Email sent successfully",
            metadata={
                "email_delivery_id": str(delivery.id),
                "provider_message_id": result.provider_message_id,
            },
        )