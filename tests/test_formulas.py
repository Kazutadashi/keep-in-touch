from datetime import date

from keep_in_touch.domain.formulas import days_overdue, recalculate_person
from keep_in_touch.domain.models import Person


def test_recalculate_person_sets_next_contact_and_urgency() -> None:
    person = Person(
        id="p_001",
        first_name="Jane",
        last_contacted_at=date(2026, 4, 1),
        contact_interval_days=30,
        relationship="Friend",
    )

    updated = recalculate_person(person, today=date(2026, 5, 5))

    assert updated.next_contact_at == date(2026, 5, 1)
    assert updated.urgency_score == 4.0


def test_recalculate_person_without_last_contact() -> None:
    person = Person(id="p_001", first_name="Jane")

    updated = recalculate_person(person, today=date(2026, 5, 5))

    assert updated.next_contact_at is None
    assert updated.urgency_score == 0.0


def test_days_overdue() -> None:
    person = Person(id="p_001", first_name="Jane", next_contact_at=date(2026, 4, 1))

    assert days_overdue(person, today=date(2026, 4, 3)) == 2
    assert days_overdue(person, today=date(2026, 3, 30)) == 0
