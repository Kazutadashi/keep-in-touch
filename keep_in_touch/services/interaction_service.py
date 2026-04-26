"""Interaction-related application workflows."""

from datetime import date

from keep_in_touch.domain.date_utils import utc_now
from keep_in_touch.domain.formulas import recalculate_person
from keep_in_touch.domain.models import Interaction
from keep_in_touch.domain.serialization import (
    interaction_from_record,
    interaction_to_record,
)
from keep_in_touch.services.ids import new_interaction_id
from keep_in_touch.services.people_service import PeopleService
from keep_in_touch.storage.jsonl_store import JsonlStore


class InteractionService:
    """Service for logging and listing interactions.

    Logging an interaction updates the related person's last-contacted date and
    computed fields.

    Example:
        service = InteractionService(interactions_store, people_service)
        interaction = service.log_interaction(
            person_id="p_001",
            interaction_date=date(2026, 4, 26),
            interaction_type="call",
            summary="Caught up about work.",
            today=date(2026, 4, 26),
        )
    """

    def __init__(
        self,
        interactions_store: JsonlStore,
        people_service: PeopleService,
    ) -> None:
        """Create the service from interaction storage and people workflows."""

        self.interactions_store = interactions_store
        self.people_service = people_service

    def list_interactions(self) -> list[Interaction]:
        """Return all valid interactions sorted newest first."""

        interactions: list[Interaction] = []
        for record in self.interactions_store.read_all():
            interaction = interaction_from_record(record)
            if interaction is not None:
                interactions.append(interaction)
        return sorted(interactions, key=lambda item: item.date, reverse=True)

    def list_for_person(self, person_id: str) -> list[Interaction]:
        """Return interactions for one person sorted newest first."""

        return [
            item for item in self.list_interactions() if item.person_id == person_id
        ]

    def update_interaction(self, interaction: Interaction, today: date) -> Interaction:
        """Update an existing interaction and refresh its person's contact date."""

        interactions = self.list_interactions()
        for index, existing in enumerate(interactions):
            if existing.id == interaction.id:
                interaction.person_id = existing.person_id
                interaction.created_at = interaction.created_at or existing.created_at
                interaction.updated_at = utc_now()
                interactions[index] = interaction
                self._save_interactions(interactions)
                self._refresh_person_contact_date(interaction.person_id, today)
                return interaction
        raise ValueError(f"Interaction not found: {interaction.id}")

    def delete_interaction(self, interaction_id: str, today: date) -> None:
        """Delete one interaction and refresh its person's contact date."""

        interactions = self.list_interactions()
        deleted_person_id = ""
        remaining: list[Interaction] = []
        for interaction in interactions:
            if interaction.id == interaction_id:
                deleted_person_id = interaction.person_id
            else:
                remaining.append(interaction)

        if not deleted_person_id:
            raise ValueError(f"Interaction not found: {interaction_id}")

        self._save_interactions(remaining)
        self._refresh_person_contact_date(deleted_person_id, today)

    def log_interaction(
        self,
        person_id: str,
        interaction_date: date,
        interaction_type: str,
        summary: str,
        follow_up_notes: str,
        today: date,
    ) -> Interaction:
        """Log an interaction and update the related person.

        If the new interaction is older than the current `last_contacted_at`, the
        current value is preserved. This prevents backfilled history from making the
        main list look stale.
        """

        person = self.people_service.get_person(person_id=person_id, today=today)
        if person is None:
            raise ValueError(f"Person not found: {person_id}")

        now = utc_now()
        interaction = Interaction(
            id=new_interaction_id(),
            person_id=person_id,
            date=interaction_date,
            interaction_type=interaction_type,
            summary=summary,
            follow_up_notes=follow_up_notes,
            created_at=now,
            updated_at=now,
        )

        interactions = self.list_interactions()
        interactions.append(interaction)
        self._save_interactions(interactions)

        is_new_latest_contact = (
            person.last_contacted_at is None
            or interaction_date >= person.last_contacted_at
        )
        if is_new_latest_contact:
            person.last_contacted_at = interaction_date
        person.updated_at = now
        recalculate_person(person, today)

        self.people_service.update_person(person, today=today)
        return interaction

    def delete_interactions_for_person(self, person_id: str) -> None:
        """Remove all interactions associated with one person."""

        remaining = [
            item for item in self.list_interactions() if item.person_id != person_id
        ]
        self._save_interactions(remaining)

    def _save_interactions(self, interactions: list[Interaction]) -> None:
        """Persist interactions in the store's native JSONL format."""

        self.interactions_store.write_all(
            [interaction_to_record(item) for item in interactions]
        )

    def _refresh_person_contact_date(self, person_id: str, today: date) -> None:
        """Set a person's last-contacted date from their remaining interactions."""

        person = self.people_service.get_person(person_id=person_id, today=today)
        if person is None:
            return

        dated_interactions = self.list_for_person(person_id)
        person.last_contacted_at = (
            max(interaction.date for interaction in dated_interactions)
            if dated_interactions
            else None
        )
        person.updated_at = utc_now()
        recalculate_person(person, today)
        self.people_service.update_person(person, today=today)
