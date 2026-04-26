"""People-related application workflows."""

from datetime import date

from keep_in_touch.domain.date_utils import utc_now
from keep_in_touch.domain.formulas import recalculate_person
from keep_in_touch.domain.models import Person
from keep_in_touch.domain.serialization import person_from_record, person_to_record
from keep_in_touch.services.ids import new_person_id
from keep_in_touch.storage.jsonl_store import JsonlStore


class PeopleService:
    """Service for creating, reading, updating, and deleting people.

    Args:
        people_store: JSONL store for people.

    Example:
        service = PeopleService(people_store)
        people = service.list_people(today=date.today())
    """

    def __init__(self, people_store: JsonlStore) -> None:
        """Create the service from a people JSONL store."""

        self.people_store = people_store

    def list_people(self, today: date) -> list[Person]:
        """Return all people with computed fields refreshed in memory."""

        people = [person_from_record(record) for record in self.people_store.read_all()]
        for person in people:
            recalculate_person(person, today)
        return sorted(people, key=_person_sort_key)

    def save_people(self, people: list[Person], today: date) -> None:
        """Save people after recalculating computed fields."""

        now = utc_now()
        for person in people:
            person.updated_at = now
            recalculate_person(person, today)
        self.people_store.write_all([person_to_record(person) for person in people])

    def get_person(self, person_id: str, today: date) -> Person | None:
        """Find one person by ID."""

        for person in self.list_people(today=today):
            if person.id == person_id:
                return person
        return None

    def create_person(self, person: Person, today: date) -> Person:
        """Create and persist a new person."""

        people = self.list_people(today=today)
        now = utc_now()
        if not person.id:
            person.id = new_person_id()
        person.created_at = person.created_at or now
        person.updated_at = now
        recalculate_person(person, today)
        people.append(person)
        self.people_store.write_all([person_to_record(item) for item in people])
        return person

    def update_person(self, person: Person, today: date) -> Person:
        """Update an existing person."""

        people = self.list_people(today=today)
        for index, existing in enumerate(people):
            if existing.id == person.id:
                person.created_at = person.created_at or existing.created_at
                person.updated_at = utc_now()
                recalculate_person(person, today)
                people[index] = person
                self.people_store.write_all([person_to_record(item) for item in people])
                return person
        raise ValueError(f"Person not found: {person.id}")

    def delete_person(self, person_id: str, today: date) -> None:
        """Delete a person by ID.

        Interaction cleanup is intentionally handled by `InteractionService` so the
        caller can decide whether to keep or remove historical records.
        """

        people = [
            person for person in self.list_people(today=today) if person.id != person_id
        ]
        self.people_store.write_all([person_to_record(person) for person in people])

    def recalculate_and_persist_all(self, today: date) -> None:
        """Refresh computed fields for every person and save them."""

        self.save_people(self.list_people(today=today), today=today)


def _person_sort_key(person: Person) -> tuple[int, str, str]:
    """Sort never-contacted people first, then oldest contacts."""

    has_never_contacted = 0 if person.last_contacted_at is None else 1
    last_contacted = (
        person.last_contacted_at.isoformat()
        if person.last_contacted_at
        else "0000-00-00"
    )
    return (has_never_contacted, last_contacted, person.sort_name)
