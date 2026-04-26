"""Simple contact age calculations."""

from datetime import date

from keep_in_touch.domain.models import Person

FORMULA_VERSION = 3


def recalculate_person(person: Person, today: date) -> Person:
    """Clear scheduling fields that are no longer actively calculated.

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
            relationship="Friend",
        )
        updated = recalculate_person(person, date(2026, 5, 5))
        assert updated.next_contact_at is None
        assert updated.urgency_score == 0.0
    """

    person.next_contact_at = None
    person.urgency_score = 0.0
    person.formula_version = FORMULA_VERSION
    return person


def days_since_contact(person: Person, today: date) -> int | None:
    """Return days since the person was last contacted.

    Args:
        person: Person to inspect.
        today: Date used for calculation.

    Example:
        person = Person(
            id="p_001",
            first_name="Jane",
            last_contacted_at=date(2026, 4, 1),
        )
        assert days_since_contact(person, date(2026, 4, 3)) == 2
    """

    if person.last_contacted_at is None:
        return None
    return max(0, (today - person.last_contacted_at).days)
