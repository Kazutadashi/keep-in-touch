"""Explainable contact scheduling formulas."""

from datetime import date, timedelta

from keep_in_touch.domain.models import Person
from keep_in_touch.domain.validation import normalize_contact_interval_days

FORMULA_VERSION = 2


def recalculate_person(person: Person, today: date) -> Person:
    """Recalculate computed fields for a person.

    Formula:
        next_contact_at = last_contacted_at + contact_interval_days
        days_overdue = max(0, today - next_contact_at)
        urgency_score = days_overdue

    Args:
        person: Person to update.
        today: Date used for calculation.

    Returns:
        The same `Person` instance with updated computed fields.

    Example:
        from datetime import date
        person = Person(
            id="p_001",
            first_name="Jane",
            last_name="Doe",
            last_contacted_at=date(2026, 4, 1),
            contact_interval_days=30,
            relationship="Friend",
        )
        updated = recalculate_person(person, date(2026, 5, 5))
        assert updated.next_contact_at == date(2026, 5, 1)
        assert updated.urgency_score == 4.0
    """

    person.contact_interval_days = normalize_contact_interval_days(
        person.contact_interval_days
    )

    if person.last_contacted_at is None:
        person.next_contact_at = None
        person.urgency_score = 0.0
        person.formula_version = FORMULA_VERSION
        return person

    next_contact_at = person.last_contacted_at + timedelta(
        days=person.contact_interval_days
    )
    days_late = days_overdue_from_date(next_contact_at, today)

    person.next_contact_at = next_contact_at
    person.urgency_score = float(days_late)
    person.formula_version = FORMULA_VERSION
    return person


def days_overdue(person: Person, today: date) -> int:
    """Return how many days overdue a person is.

    Args:
        person: Person to inspect.
        today: Date used for calculation.

    Example:
        person = Person(
            id="p_001",
            first_name="Jane",
            next_contact_at=date(2026, 4, 1),
        )
        assert days_overdue(person, date(2026, 4, 3)) == 2
    """

    if person.next_contact_at is None:
        return 0
    return days_overdue_from_date(person.next_contact_at, today)


def days_overdue_from_date(next_contact_at: date, today: date) -> int:
    """Return overdue days for a specific next-contact date.

    Example:
        assert days_overdue_from_date(date(2026, 4, 1), date(2026, 4, 3)) == 2
        assert days_overdue_from_date(date(2026, 4, 1), date(2026, 3, 30)) == 0
    """

    return max(0, (today - next_contact_at).days)
