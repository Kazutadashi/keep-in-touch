"""Small date parsing and formatting helpers."""

from datetime import date, datetime, timezone


def today_local() -> date:
    """Return today's local date.

    Example:
        today = today_local()
        assert isinstance(today, date)
    """

    return date.today()


def utc_now() -> datetime:
    """Return the current UTC time without microseconds.

    The app stores timestamps in ISO 8601 format. UTC keeps storage predictable
    without requiring a sync service or user account.

    Example:
        now = utc_now()
        assert now.tzinfo is not None
    """

    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_date(value: object) -> date | None:
    """Parse a `YYYY-MM-DD` date string.

    Args:
        value: Date-like value. Invalid values return None.

    Returns:
        A date or None.

    Example:
        assert parse_date("2026-04-26") == date(2026, 4, 26)
        assert parse_date("") is None
    """

    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def parse_datetime(value: object) -> datetime | None:
    """Parse an ISO 8601 datetime string.

    Args:
        value: Datetime-like value. Invalid values return None.

    Returns:
        A datetime or None.

    Example:
        parsed = parse_datetime("2026-04-26T12:00:00+00:00")
        assert parsed is not None
    """

    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def date_to_string(value: date | None) -> str | None:
    """Convert a date to an ISO string.

    Example:
        assert date_to_string(date(2026, 4, 26)) == "2026-04-26"
    """

    return value.isoformat() if value is not None else None


def datetime_to_string(value: datetime | None) -> str | None:
    """Convert a datetime to an ISO string.

    Example:
        assert datetime_to_string(None) is None
    """

    return value.isoformat() if value is not None else None
