from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.jobs.enums import JobStatus
from app.infrastructure.database.models.job_model import JobModel


class MetricsQueries:
    """
    Application query service for simple operational metrics.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_jobs_summary(self) -> dict[str, int]:
        """
        Return a count of jobs grouped by status.
        """
        summary = {status.value: 0 for status in JobStatus}

        stmt = (
            select(JobModel.status, func.count(JobModel.id))
            .group_by(JobModel.status)
        )

        rows = self.session.execute(stmt).all()

        total = 0

        for status, count in rows:
            summary[status] = count
            total += count

        summary["TOTAL"] = total

        return summary