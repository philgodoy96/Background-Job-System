from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.domain.jobs.enums import JobStatus, JobType
from app.infrastructure.database.base import Base


class JobModel(Base):
    """
    SQLAlchemy model for the jobs table.

    A job represents one unit of asynchronous work.
    """

    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    queue_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="default",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=JobStatus.PENDING.value,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )

    locked_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    locked_by_run_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_error_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    last_error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    attempts = relationship(
        "JobAttemptModel",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_jobs_claimable",
            "queue_name",
            "status",
            "available_at",
            "priority",
        ),
        Index(
            "ix_jobs_locked_until",
            "status",
            "locked_until",
        ),
        Index(
            "ix_jobs_idempotency_key",
            "idempotency_key",
        ),
    )

    @property
    def job_status(self) -> JobStatus:
        return JobStatus(self.status)

    @property
    def job_type(self) -> JobType:
        return JobType(self.type)