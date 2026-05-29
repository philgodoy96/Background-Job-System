from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.side_effects.enums import EmailDeliveryStatus


@dataclass
class EmailDelivery:
    id: UUID
    idempotency_key: str
    recipient: str
    template: str
    status: EmailDeliveryStatus
    provider_message_id: str | None
    created_at: datetime
    updated_at: datetime
    sent_at: datetime | None

    def already_sent(self) -> bool:
        return self.status == EmailDeliveryStatus.SENT

    def is_ambiguous(self) -> bool:
        return self.status == EmailDeliveryStatus.UNKNOWN

    def is_in_progress(self) -> bool:
        return self.status == EmailDeliveryStatus.PROCESSING