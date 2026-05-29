from datetime import UTC, datetime, timedelta


def utc_now() -> datetime:
    """
    Return the current timezone-aware UTC datetime.
    """
    return datetime.now(UTC)


def seconds_from_now(seconds: int) -> datetime:
    """
    Return a timezone-aware UTC datetime N seconds from now.
    """
    return utc_now() + timedelta(seconds=seconds)


def milliseconds_between(started_at: datetime, finished_at: datetime) -> int:
    """
    Return the duration between two datetimes in milliseconds.
    """
    delta = finished_at - started_at
    return int(delta.total_seconds() * 1000)