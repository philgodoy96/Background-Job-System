from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.side_effects.enums import EmailDeliveryStatus


@dataclass(slots=True)
class EmailDelivery:
    """
    Domain representation of an email delivery side effect.

    This entity is used to make email sending idempotent.
    """

    id: UUID
    idempotency_key: str
    recipient: str
    template: str
    status: EmailDeliveryStatus
    provider_message_id: str | None
    created_at: datetime
    updated_at: datetime
    sent_at: datetime | None

    @property
    def is_sent(self) -> bool:
        return self.status == EmailDeliveryStatus.SENT

    @property
    def is_unknown(self) -> bool:
        return self.status == EmailDeliveryStatus.UNKNOWN

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            EmailDeliveryStatus.SENT,
            EmailDeliveryStatus.FAILED,
            EmailDeliveryStatus.UNKNOWN,
        }