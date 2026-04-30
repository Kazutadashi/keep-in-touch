from datetime import date

from keep_in_touch.domain.models import Person
from keep_in_touch.domain.person_filters import PeopleFilterCriteria, filter_people


def test_filter_people_searches_tags_case_insensitively() -> None:
    people = [
        Person(id="p_001", first_name="Amina", tags=["Friend", "Python"]),
        Person(id="p_002", first_name="Ben", tags=["Coworker"]),
    ]

    filtered = filter_people(people, PeopleFilterCriteria(search_text="python"))

    assert [person.id for person in filtered] == ["p_001"]


def test_filter_people_by_last_contact_date_range() -> None:
    people = [
        Person(
            id="p_001",
            first_name="Amina",
            last_contacted_at=date(2026, 4, 20),
        ),
        Person(
            id="p_002",
            first_name="Ben",
            last_contacted_at=date(2026, 3, 1),
        ),
        Person(id="p_003", first_name="Clara"),
    ]

    filtered = filter_people(
        people,
        PeopleFilterCriteria(
            last_contacted_from=date(2026, 4, 1),
            last_contacted_to=date(2026, 4, 30),
        ),
    )

    assert [person.id for person in filtered] == ["p_001"]


def test_filter_people_by_birthday_month() -> None:
    people = [
        Person(id="p_001", first_name="Amina", birthday=date(1990, 2, 18)),
        Person(id="p_002", first_name="Ben", birthday=date(1988, 11, 3)),
        Person(id="p_003", first_name="Clara"),
    ]

    filtered = filter_people(people, PeopleFilterCriteria(birthday_month=11))

    assert [person.id for person in filtered] == ["p_002"]


def test_filter_people_searches_name_notes_and_handles() -> None:
    people = [
        Person(
            id="p_001",
            first_name="Amina",
            notes="Ask about the workshop.",
        ),
        Person(
            id="p_002",
            first_name="Ben",
            socials={"github": "billing-ben"},
        ),
    ]

    filtered = filter_people(people, PeopleFilterCriteria(search_text="billing"))

    assert [person.id for person in filtered] == ["p_002"]
