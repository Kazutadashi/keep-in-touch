"""Import and export workflows."""

from datetime import date
from pathlib import Path
from typing import Any

from keep_in_touch.domain.models import Person, SOCIAL_PLATFORMS
from keep_in_touch.domain.serialization import (
    interaction_to_record,
    person_from_record,
    person_to_record,
    split_full_name,
)
from keep_in_touch.services.ids import new_person_id
from keep_in_touch.services.interaction_service import InteractionService
from keep_in_touch.services.people_service import PeopleService
from keep_in_touch.storage.csv_io import read_csv, write_csv

PEOPLE_CSV_FIELDS = [
    "id",
    "first_name",
    "last_name",
    "nickname",
    "bio",
    "birthday",
    "tags",
    "relationship",
    "preferred_contact_method",
    *[f"social_{key}" for key, _label in SOCIAL_PLATFORMS],
    "contact_interval_days",
    "last_contacted_at",
    "next_contact_at",
    "urgency_score",
    "notes",
]

INTERACTION_CSV_FIELDS = [
    "id",
    "person_id",
    "date",
    "interaction_type",
    "summary",
    "follow_up_notes",
]


class ImportExportService:
    """Service for CSV import/export.

    Args:
        people_service: People service.
        interaction_service: Interaction service.

    Example:
        service.export_people_csv(Path("people.csv"), today=date.today())
    """

    def __init__(
        self,
        people_service: PeopleService,
        interaction_service: InteractionService,
    ) -> None:
        """Create the service from people and interaction workflows."""

        self.people_service = people_service
        self.interaction_service = interaction_service

    def export_people_csv(self, path: Path, today: date) -> None:
        """Export people to CSV."""

        rows = [
            _person_csv_row(person)
            for person in self.people_service.list_people(today)
        ]
        write_csv(path, rows, PEOPLE_CSV_FIELDS)

    def export_interactions_csv(self, path: Path) -> None:
        """Export interactions to CSV."""

        rows = [
            interaction_to_record(interaction)
            for interaction in self.interaction_service.list_interactions()
        ]
        write_csv(path, rows, INTERACTION_CSV_FIELDS)

    def import_people_csv(self, path: Path, today: date) -> list[Person]:
        """Forgiving people CSV import.

        The importer accepts columns that match the native field names. Missing IDs
        are generated automatically. Rows without a first or last name are skipped.
        """

        imported: list[Person] = []
        existing = self.people_service.list_people(today=today)
        existing_by_id = {person.id: person for person in existing}

        for row in read_csv(path):
            record = _normalize_people_csv_row(row)
            if not record.get("first_name") and not record.get("last_name"):
                continue
            if not record.get("id"):
                record["id"] = new_person_id()

            person = person_from_record(record)

            if person.id in existing_by_id:
                person.created_at = existing_by_id[person.id].created_at
                existing_by_id[person.id] = person
            else:
                existing.append(person)
                existing_by_id[person.id] = person

            imported.append(person)

        self.people_service.save_people(list(existing_by_id.values()), today=today)
        return imported


def _normalize_people_csv_row(row: dict[str, str]) -> dict[str, Any]:
    """Map simple CSV rows into native person record fields.

    This function intentionally handles a few friendly aliases. More sophisticated
    column mapping can be added later without changing the storage layer.
    """

    aliases = {
        "firstname": "first_name",
        "first": "first_name",
        "given_name": "first_name",
        "lastname": "last_name",
        "last": "last_name",
        "surname": "last_name",
        "family_name": "last_name",
        "full_name": "name",
        "person": "name",
        "last_contact": "last_contacted_at",
        "last_contacted": "last_contacted_at",
        "frequency_days": "contact_interval_days",
        "interval_days": "contact_interval_days",
        "method": "preferred_contact_method",
        "relationship_type": "relationship",
        "category": "relationship",
        "connection_type": "relationship",
    }

    normalized: dict[str, Any] = {}
    socials: dict[str, str] = {}
    for key, value in row.items():
        clean_key = key.strip().lower().replace(" ", "_")
        if clean_key.startswith("social_"):
            platform = clean_key.removeprefix("social_")
            handle = value.strip() if isinstance(value, str) else value
            if platform and handle:
                socials[platform] = str(handle)
            continue

        target = aliases.get(clean_key, clean_key)
        normalized[target] = value.strip() if isinstance(value, str) else value

    missing_split_name = (
        "first_name" not in normalized and "last_name" not in normalized
    )
    if missing_split_name and normalized.get("name"):
        first_name, last_name = split_full_name(normalized["name"])
        normalized["first_name"] = first_name
        normalized["last_name"] = last_name

    if socials:
        normalized["socials"] = socials

    return normalized


def _person_csv_row(person: Person) -> dict[str, Any]:
    """Return a flattened CSV row for a person."""

    row = person_to_record(person)
    socials = person.socials
    for platform, _label in SOCIAL_PLATFORMS:
        row[f"social_{platform}"] = socials.get(platform, "")
    row.pop("socials", None)
    return row
