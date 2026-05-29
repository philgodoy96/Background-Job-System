from enum import StrEnum


class EmailDeliveryStatus(StrEnum):
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    UNKNOWN = "unknown"