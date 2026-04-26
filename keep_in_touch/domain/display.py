"""Display-oriented helpers for domain models."""

from datetime import date

from keep_in_touch.domain.models import Person


def middle_name(person: Person) -> str:
    """Return middle-name data from future-compatible extra fields.

    The current schema does not have a dedicated middle-name field. Preserving
    this lookup in one place lets the UI support future data without spreading
    schema guesses through widgets.
    """

    value = person.extra_fields.get(
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


def date_text(value: date | None, fallback: str = "-") -> str:
    """Return an ISO date string or fallback text."""

    return value.isoformat() if value else fallback


def contact_status(person: Person, today: date | None = None) -> str:
    """Return a compact human-readable contact status.

    Args:
        person: Person with recalculated contact fields.
        today: Optional date for future/past wording. When omitted, overdue
            status uses the person's recalculated urgency score.
    """

    if person.last_contacted_at is None:
        return "Never contacted"
    if person.next_contact_at is None:
        return "Not scheduled"

    if today is None:
        if person.urgency_score > 0:
            return _overdue_text(int(person.urgency_score))
        return "On schedule"

    days_until_contact = (person.next_contact_at - today).days
    if days_until_contact < 0:
        return _overdue_text(abs(days_until_contact))
    if days_until_contact == 0:
        return "Due today"

    suffix = "day" if days_until_contact == 1 else "days"
    return f"In {days_until_contact} {suffix}"


def _overdue_text(days: int) -> str:
    """Return overdue display text for a number of days."""

    suffix = "day" if days == 1 else "days"
    return f"{days} {suffix} overdue"
