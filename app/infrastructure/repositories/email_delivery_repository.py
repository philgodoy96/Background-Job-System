from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.domain.side_effects.entities import EmailDelivery
from app.domain.side_effects.enums import EmailDeliveryStatus
from app.infrastructure.database.models.email_delivery_model import (
    EmailDeliveryModel,
)


class EmailDeliveryRepository:
    """
    Repository for email delivery side-effect persistence.

    This repository supports local idempotency for email sending.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> EmailDelivery | None:
        """
        Return an email delivery by idempotency key.
        """
        stmt = select(EmailDeliveryModel).where(
            EmailDeliveryModel.idempotency_key == idempotency_key
        )

        model = self.session.scalars(stmt).first()

        if model is None:
            return None

        return self._to_domain(model)

    def get_or_create(
        self,
        *,
        idempotency_key: str,
        recipient: str,
        template: str,
    ) -> EmailDelivery:
        """
        Get an existing email delivery or create a new one.

        This uses PostgreSQL ON CONFLICT DO NOTHING to make creation safe when
        two transactions race on the same idempotency key.
        """
        now = utc_now()

        insert_stmt = (
            insert(EmailDeliveryModel)
            .values(
                idempotency_key=idempotency_key,
                recipient=recipient,
                template=template,
                status=EmailDeliveryStatus.PENDING.value,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_nothing(
                index_elements=["idempotency_key"],
            )
            .returning(EmailDeliveryModel.id)
        )

        inserted_id = self.session.execute(insert_stmt).scalar_one_or_none()
        self.session.flush()

        if inserted_id is not None:
            model = self.session.get(EmailDeliveryModel, inserted_id)
        else:
            model = self.session.scalars(
                select(EmailDeliveryModel).where(
                    EmailDeliveryModel.idempotency_key == idempotency_key
                )
            ).one()

        return self._to_domain(model)

    def mark_sent(
        self,
        *,
        delivery_id: UUID,
        provider_message_id: str,
    ) -> bool:
        """
        Mark an email delivery as SENT.
        """
        now = utc_now()

        stmt = (
            update(EmailDeliveryModel)
            .where(EmailDeliveryModel.id == delivery_id)
            .values(
                status=EmailDeliveryStatus.SENT.value,
                provider_message_id=provider_message_id,
                sent_at=now,
                updated_at=now,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def mark_failed(
        self,
        *,
        delivery_id: UUID,
    ) -> bool:
        """
        Mark an email delivery as FAILED.
        """
        now = utc_now()

        stmt = (
            update(EmailDeliveryModel)
            .where(EmailDeliveryModel.id == delivery_id)
            .values(
                status=EmailDeliveryStatus.FAILED.value,
                updated_at=now,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def mark_unknown(
        self,
        *,
        delivery_id: UUID,
    ) -> bool:
        """
        Mark an email delivery as UNKNOWN.

        UNKNOWN means the external provider may have accepted the operation,
        but the worker did not receive a definitive response.
        """
        now = utc_now()

        stmt = (
            update(EmailDeliveryModel)
            .where(EmailDeliveryModel.id == delivery_id)
            .values(
                status=EmailDeliveryStatus.UNKNOWN.value,
                updated_at=now,
            )
        )

        result = self.session.execute(stmt)
        self.session.flush()

        return result.rowcount == 1

    def _to_domain(self, model: EmailDeliveryModel) -> EmailDelivery:
        """
        Convert a SQLAlchemy model into a domain EmailDelivery entity.
        """
        return EmailDelivery(
            id=model.id,
            idempotency_key=model.idempotency_key,
            recipient=model.recipient,
            template=model.template,
            status=EmailDeliveryStatus(model.status),
            provider_message_id=model.provider_message_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            sent_at=model.sent_at,
        )