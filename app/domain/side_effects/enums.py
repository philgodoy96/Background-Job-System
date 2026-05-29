from enum import StrEnum


class EmailDeliveryStatus(StrEnum):
    """
    Status of an email delivery side effect.
    """

    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"