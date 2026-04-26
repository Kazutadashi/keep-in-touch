from datetime import date

from keep_in_touch.domain.models import Person
from keep_in_touch.services.interaction_service import InteractionService
from keep_in_touch.services.people_service import PeopleService
from keep_in_touch.storage.jsonl_store import JsonlStore


def test_logging_interaction_updates_person(tmp_path) -> None:
    people_store = JsonlStore(tmp_path / "people.jsonl")
    interactions_store = JsonlStore(tmp_path / "interactions.jsonl")
    people_service = PeopleService(people_store)
    interaction_service = InteractionService(interactions_store, people_service)

    person = people_service.create_person(
        Person(
            id="p_001",
            first_name="Jane",
            last_name="Doe",
            contact_interval_days=30,
            relationship="Friend",
        ),
        today=date(2026, 4, 1),
    )

    interaction_service.log_interaction(
        person_id=person.id,
        interaction_date=date(2026, 4, 10),
        interaction_type="call",
        summary="Caught up.",
        follow_up_notes="Ask about new project.",
        today=date(2026, 4, 10),
    )

    updated = people_service.get_person(person.id, today=date(2026, 4, 10))
    assert updated is not None
    assert updated.last_contacted_at == date(2026, 4, 10)
    assert updated.next_contact_at == date(2026, 5, 10)

    interactions = interaction_service.list_for_person(person.id)
    assert len(interactions) == 1
    assert interactions[0].summary == "Caught up."
