"""Display-oriented helpers for domain models."""

from datetime import date

from keep_in_touch.domain.formulas import days_since_contact
from keep_in_touch.domain.models import (
    PREFERRED_CONTACT_METHOD_OPTIONS,
    Person,
    SOCIAL_PLATFORMS,
)


def middle_name(person: Person) -> str:
    """Return the person's middle name with legacy fallback support."""

    value = person.middle_name or person.extra_fields.get(
        "middle_name",
        person.extra_fields.get("middle", ""),
    )
    return str(value).strip()


def display_name(person: Person) -> str:
    """Return a display name using first, optional middle, and last name."""

    parts = [person.first_name, middle_name(person), person.last_name]
    return " ".join(part.strip() for part in parts if part.strip()) or "(Unnamed)"


def tags_text(person: Person, fallback: str = "-") -> str:
    """Return comma-separated tags for display."""

    return ", ".join(person.tags) if person.tags else fallback


def social_lines(person: Person) -> list[tuple[str, str]]:
    """Return social handles as display label/value pairs.

    Known platforms are returned in UI order. Unknown platforms are included
    afterward so data from newer versions is still visible.
    """

    known_keys = {key for key, _label in SOCIAL_PLATFORMS}
    lines = [
        (label, person.socials[key])
        for key, label in SOCIAL_PLATFORMS
        if person.socials.get(key)
    ]
    lines.extend(
        (key.replace("_", " ").title(), value)
        for key, value in sorted(person.socials.items())
        if key not in known_keys and value
    )
    return lines


def date_text(value: date | None, fallback: str = "-") -> str:
    """Return an ISO date string or fallback text."""

    return value.isoformat() if value else fallback


def days_since_contact_text(person: Person, today: date) -> str:
    """Return a compact days-since-contact value for display."""

    days = days_since_contact(person, today)
    if days is None:
        return "Never"
    if days == 0:
        return "Today"
    suffix = "day" if days == 1 else "days"
    return f"{days} {suffix}"


def contact_age_text(person: Person, today: date) -> str:
    """Return a sentence-like contact age value for detail views."""

    days = days_since_contact(person, today)
    if days is None:
        return "Never contacted"
    if days == 0:
        return "Contacted today"
    suffix = "day" if days == 1 else "days"
    return f"{days} {suffix} since contact"


def contact_method_label(value: str, fallback: str = "-") -> str:
    """Return a friendly label for a stored preferred contact method key."""

    clean_value = value.strip()
    if not clean_value:
        return fallback

    labels = {
        key.casefold(): label for key, label in PREFERRED_CONTACT_METHOD_OPTIONS
    }
    return labels.get(clean_value.casefold(), clean_value.replace("_", " ").title())
