from pydantic import BaseModel


class JobsSummaryResponse(BaseModel):
    """
    Simple jobs summary grouped by status.
    """

    PENDING: int
    RUNNING: int
    RETRY_SCHEDULED: int
    SUCCEEDED: int
    DEAD_LETTER: int
    CANCELLED: int
    TOTAL: int