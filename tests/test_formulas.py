from datetime import date

from keep_in_touch.domain.formulas import days_since_contact, recalculate_person
from keep_in_touch.domain.models import Person


def test_recalculate_person_clears_scheduling_fields() -> None:
    person = Person(
        id="p_001",
        first_name="Jane",
        last_contacted_at=date(2026, 4, 1),
        next_contact_at=date(2026, 5, 1),
        urgency_score=4.0,
        relationship="Friend",
    )

    updated = recalculate_person(person, today=date(2026, 5, 5))

    assert updated.next_contact_at is None
    assert updated.urgency_score == 0.0


def test_recalculate_person_without_last_contact() -> None:
    person = Person(id="p_001", first_name="Jane")

    updated = recalculate_person(person, today=date(2026, 5, 5))

    assert updated.next_contact_at is None
    assert updated.urgency_score == 0.0


def test_days_since_contact() -> None:
    person = Person(
        id="p_001",
        first_name="Jane",
        last_contacted_at=date(2026, 4, 1),
    )

    assert days_since_contact(person, today=date(2026, 4, 3)) == 2
    assert days_since_contact(person, today=date(2026, 3, 30)) == 0
    assert (
        days_since_contact(Person(id="p_002", first_name="Jim"), date(2026, 4, 3))
        is None
    )
