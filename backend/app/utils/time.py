from datetime import datetime, timezone


def utcnow_naive() -> datetime:
    """Returns the current UTC time as a naive datetime (no timezone info)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
