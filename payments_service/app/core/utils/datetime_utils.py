from datetime import datetime, timezone
from typing import Optional

def normalize_to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensures a datetime is offset-aware and in UTC.
    If it's naive, assumes UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def now_utc() -> datetime:
    """Returns the current aware UTC datetime."""
    return datetime.now(timezone.utc)

def is_expired(expires_at: datetime) -> bool:
    """
    Checks if a datetime is in the past compared to current UTC time.
    Handles naive/aware comparison by normalizing.
    """
    return normalize_to_utc(expires_at) < now_utc()
