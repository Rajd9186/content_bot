from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime.

    This is the single source of truth for all datetime generation
    in the application. Using this consistently prevents timezone
    mismatch errors (offset-naive vs offset-aware).
    """
    return datetime.now(timezone.utc)


def utc_now_naive() -> datetime:
    """Return the current UTC time as a timezone-naive datetime.

    Use only when interacting with legacy columns or third-party
    libraries that do not support timezone-aware datetimes.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
