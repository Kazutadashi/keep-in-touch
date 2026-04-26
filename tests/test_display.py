from datetime import date

from keep_in_touch.domain.display import birthday_text, days_until_birthday
from keep_in_touch.domain.models import Person


def test_days_until_birthday_returns_zero_for_today() -> None:
    person = Person(
        id="p_001",
        first_name="Jane",
        birthday=date(1992, 4, 26),
    )

    assert days_until_birthday(person, date(2026, 4, 26)) == 0
    assert birthday_text(person, date(2026, 4, 26)) == "Today"


def test_days_until_birthday_wraps_to_next_year() -> None:
    person = Person(
        id="p_001",
        first_name="Jane",
        birthday=date(1992, 1, 1),
    )

    assert days_until_birthday(person, date(2026, 4, 26)) == 250
    assert birthday_text(person, date(2026, 4, 26)) == "Jan 1"


def test_days_until_birthday_handles_leap_day_on_non_leap_year() -> None:
    person = Person(
        id="p_001",
        first_name="Jane",
        birthday=date(1992, 2, 29),
    )

    assert days_until_birthday(person, date(2026, 2, 28)) == 1
    assert birthday_text(person, date(2026, 2, 28)) == "Tomorrow"
