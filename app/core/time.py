from datetime import UTC, datetime, timedelta


def utc_now() -> datetime:
    """
    Return the current timezone-aware UTC datetime.
    """
    return datetime.now(UTC)


def seconds_from_now(seconds: int) -> datetime:
    """
    Return a UTC datetime N seconds from now.
    """
    return utc_now() + timedelta(seconds=seconds)