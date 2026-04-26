"""Input normalization helpers.

These helpers are intentionally small and predictable. Validation should make data
safe without surprising the user.
"""

from keep_in_touch.domain.models import RELATIONSHIP_OPTIONS


def normalize_relationship(value: object, default: str = "Friend") -> str:
    """Normalize a relationship category into display-friendly text.

    The app ships with default categories such as "Friend" and "Classmate", but
    custom categories are allowed. This keeps the data text-based and flexible.

    Args:
        value: User-provided relationship value.
        default: Value used when the relationship is empty.

    Example:
        assert normalize_relationship(" classmate ") == "Classmate"
        assert normalize_relationship("") == "Friend"
        assert normalize_relationship("mentor") == "Mentor"
    """

    text = normalize_text(value)
    if not text:
        return default

    known = {option.lower(): option for option in RELATIONSHIP_OPTIONS}
    return known.get(text.lower(), text[:1].upper() + text[1:])


def normalize_contact_interval_days(value: object, default: int = 30) -> int:
    """Normalize contact interval to a positive number of days.

    Example:
        assert normalize_contact_interval_days("14") == 14
        assert normalize_contact_interval_days("0") == 1
    """

    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        parsed = default
    return max(1, parsed)


def normalize_tags(value: object) -> list[str]:
    """Normalize tags from a list or comma-separated string.

    Example:
        assert normalize_tags("friend, college") == ["friend", "college"]
        assert normalize_tags(["Friend", ""]) == ["Friend"]
    """

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def normalize_socials(value: object) -> dict[str, str]:
    """Normalize social handles from a mapping.

    Empty handles are removed. Keys are lowercased and stripped so storage stays
    predictable while still allowing future platform names.

    Example:
        assert normalize_socials({"Discord": " jane "}) == {"discord": "jane"}
    """

    if not isinstance(value, dict):
        return {}

    socials: dict[str, str] = {}
    for key, handle in value.items():
        platform = normalize_text(key).lower()
        text = normalize_text(handle)
        if platform and text:
            socials[platform] = text
    return socials


def normalize_text(value: object) -> str:
    """Convert a value to stripped text.

    Example:
        assert normalize_text(" Jane ") == "Jane"
        assert normalize_text(None) == ""
    """

    if value is None:
        return ""
    return str(value).strip()
