from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.domain.jobs.enums import AttemptStatus
from app.infrastructure.database.base import Base


class JobAttemptModel(Base):
    """
    SQLAlchemy model for the job_attempts table.

    A job attempt represents one execution attempt of a job.
    """

    __tablename__ = "job_attempts"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    job_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )

    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    worker_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    worker_run_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=AttemptStatus.STARTED.value,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    error_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    job = relationship(
        "JobModel",
        back_populates="attempts",
    )

    __table_args__ = (
        Index(
            "ix_job_attempts_job_id",
            "job_id",
        ),
        Index(
            "ix_job_attempts_job_id_attempt_number",
            "job_id",
            "attempt_number",
            unique=True,
        ),
    )