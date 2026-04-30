"""Filtering helpers for the people list."""

from dataclasses import dataclass
from datetime import date

from keep_in_touch.domain.display import display_name
from keep_in_touch.domain.models import Person


@dataclass(frozen=True)
class PeopleFilterCriteria:
    """Values used to narrow the people shown in the main table."""

    search_text: str = ""
    last_contacted_from: date | None = None
    last_contacted_to: date | None = None
    birthday_month: int | None = None


def filter_people(
    people: list[Person],
    criteria: PeopleFilterCriteria,
) -> list[Person]:
    """Return people matching the provided filter values."""

    return [person for person in people if person_matches_filters(person, criteria)]


def person_matches_filters(person: Person, criteria: PeopleFilterCriteria) -> bool:
    """Return whether one person satisfies the people-table filters."""

    query = criteria.search_text.strip().casefold()
    if query and query not in _searchable_text(person):
        return False

    if not _date_in_range(
        person.last_contacted_at,
        criteria.last_contacted_from,
        criteria.last_contacted_to,
    ):
        return False

    if (
        criteria.birthday_month is not None
        and (
            person.birthday is None
            or person.birthday.month != criteria.birthday_month
        )
    ):
        return False

    return True


def _searchable_text(person: Person) -> str:
    """Return lower-cased text searched by the quick filter."""

    values = [
        display_name(person),
        person.nickname,
        person.email,
        person.phone,
        person.relationship,
        person.preferred_contact_method,
        person.bio,
        person.notes,
        " ".join(person.tags),
    ]
    values.extend(person.socials.values())
    return " ".join(value for value in values if value).casefold()


def _date_in_range(
    value: date | None,
    start: date | None,
    end: date | None,
) -> bool:
    """Return whether an optional date falls within an optional inclusive range."""

    if start is None and end is None:
        return True
    if value is None:
        return False
    if start is not None and value < start:
        return False
    return end is None or value <= end
