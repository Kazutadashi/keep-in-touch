"""Convert domain models to and from JSON-compatible records."""

from collections.abc import Mapping
from typing import Any

from keep_in_touch.domain.date_utils import (
    date_to_string,
    datetime_to_string,
    parse_date,
    parse_datetime,
)
from keep_in_touch.domain.models import Interaction, Person
from keep_in_touch.domain.validation import (
    normalize_contact_interval_days,
    normalize_relationship,
    normalize_socials,
    normalize_tags,
    normalize_text,
)

PERSON_FIELDS = {
    "schema_version",
    "id",
    "name",  # Legacy field. Read during migration; do not write.
    "first_name",
    "last_name",
    "nickname",
    "bio",
    "birthday",
    "tags",
    "relationship",
    "relationship_type",  # Legacy field name. Read during migration; do not write.
    "importance",  # Legacy field. Ignored because relationship is categorical now.
    "preferred_contact_method",
    "socials",
    "contact_interval_days",
    "last_contacted_at",
    "next_contact_at",
    "urgency_score",
    "notes",
    "formula_version",
    "created_at",
    "updated_at",
}

INTERACTION_FIELDS = {
    "schema_version",
    "id",
    "person_id",
    "date",
    "interaction_type",
    "summary",
    "follow_up_notes",
    "created_at",
    "updated_at",
}


def person_from_record(record: Mapping[str, Any]) -> Person:
    """Create a `Person` from a JSON-compatible mapping.

    Missing fields receive defaults. Unknown fields are saved in `extra_fields` so
    future app versions do not lose data.

    Legacy records using `name` are migrated into `first_name` and `last_name`.
    Legacy records using `relationship_type` are migrated to `relationship`.

    Example:
        person = person_from_record({"id": "p_001", "name": "Jane Doe"})
        assert person.first_name == "Jane"
        assert person.last_name == "Doe"
    """

    extra_fields = {
        key: value for key, value in record.items() if key not in PERSON_FIELDS
    }

    first_name = normalize_text(record.get("first_name"))
    last_name = normalize_text(record.get("last_name"))

    if not first_name and not last_name:
        first_name, last_name = split_full_name(record.get("name"))

    relationship_value = record.get("relationship", record.get("relationship_type"))

    return Person(
        schema_version=_int_from_record(record, "schema_version", 1),
        id=normalize_text(record.get("id")),
        first_name=first_name,
        last_name=last_name,
        nickname=normalize_text(record.get("nickname")),
        bio=normalize_text(record.get("bio")),
        birthday=parse_date(record.get("birthday")),
        tags=normalize_tags(record.get("tags")),
        relationship=normalize_relationship(relationship_value),
        preferred_contact_method=normalize_text(record.get("preferred_contact_method")),
        socials=normalize_socials(record.get("socials")),
        contact_interval_days=normalize_contact_interval_days(
            record.get("contact_interval_days", 30)
        ),
        last_contacted_at=parse_date(record.get("last_contacted_at")),
        next_contact_at=parse_date(record.get("next_contact_at")),
        urgency_score=_float_from_record(record, "urgency_score", 0.0),
        notes=normalize_text(record.get("notes")),
        formula_version=_int_from_record(record, "formula_version", 1),
        created_at=parse_datetime(record.get("created_at")),
        updated_at=parse_datetime(record.get("updated_at")),
        extra_fields=extra_fields,
    )


def person_to_record(person: Person) -> dict[str, Any]:
    """Convert a `Person` to a JSON-compatible dictionary.

    Example:
        person = Person(id="p_001", first_name="Jane", last_name="Doe")
        record = person_to_record(person)
        assert record["first_name"] == "Jane"
        assert record["last_name"] == "Doe"
    """

    record: dict[str, Any] = dict(person.extra_fields)
    record.update(
        {
            "schema_version": person.schema_version,
            "id": person.id,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "nickname": person.nickname,
            "bio": person.bio,
            "birthday": date_to_string(person.birthday),
            "tags": person.tags,
            "relationship": person.relationship,
            "preferred_contact_method": person.preferred_contact_method,
            "socials": person.socials,
            "contact_interval_days": person.contact_interval_days,
            "last_contacted_at": date_to_string(person.last_contacted_at),
            "next_contact_at": date_to_string(person.next_contact_at),
            "urgency_score": person.urgency_score,
            "notes": person.notes,
            "formula_version": person.formula_version,
            "created_at": datetime_to_string(person.created_at),
            "updated_at": datetime_to_string(person.updated_at),
        }
    )
    return {key: value for key, value in record.items() if value is not None}


def interaction_from_record(record: Mapping[str, Any]) -> Interaction | None:
    """Create an `Interaction` from a JSON-compatible mapping.

    Returns None when required fields are missing or invalid.

    Example:
        interaction = interaction_from_record(
            {"id": "i_001", "person_id": "p_001", "date": "2026-04-26"}
        )
        assert interaction is not None
    """

    interaction_date = parse_date(record.get("date"))
    if interaction_date is None:
        return None

    interaction_id = normalize_text(record.get("id"))
    person_id = normalize_text(record.get("person_id"))
    if not interaction_id or not person_id:
        return None

    extra_fields = {
        key: value for key, value in record.items() if key not in INTERACTION_FIELDS
    }
    return Interaction(
        schema_version=_int_from_record(record, "schema_version", 1),
        id=interaction_id,
        person_id=person_id,
        date=interaction_date,
        interaction_type=normalize_text(record.get("interaction_type")),
        summary=normalize_text(record.get("summary")),
        follow_up_notes=normalize_text(record.get("follow_up_notes")),
        created_at=parse_datetime(record.get("created_at")),
        updated_at=parse_datetime(record.get("updated_at")),
        extra_fields=extra_fields,
    )


def interaction_to_record(interaction: Interaction) -> dict[str, Any]:
    """Convert an `Interaction` to a JSON-compatible dictionary.

    Example:
        interaction = Interaction(
            id="i_001",
            person_id="p_001",
            date=parse_date("2026-04-26"),
        )
        assert interaction_to_record(interaction)["person_id"] == "p_001"
    """

    record: dict[str, Any] = dict(interaction.extra_fields)
    record.update(
        {
            "schema_version": interaction.schema_version,
            "id": interaction.id,
            "person_id": interaction.person_id,
            "date": date_to_string(interaction.date),
            "interaction_type": interaction.interaction_type,
            "summary": interaction.summary,
            "follow_up_notes": interaction.follow_up_notes,
            "created_at": datetime_to_string(interaction.created_at),
            "updated_at": datetime_to_string(interaction.updated_at),
        }
    )
    return {key: value for key, value in record.items() if value is not None}


def split_full_name(value: object) -> tuple[str, str]:
    """Split a legacy full name into first and last name fields.

    The first token becomes `first_name`. Everything after it becomes `last_name`.

    Args:
        value: Full name-like value.

    Example:
        assert split_full_name("Jane Doe") == ("Jane", "Doe")
        assert split_full_name("Prince") == ("Prince", "")
        assert split_full_name("") == ("", "")
    """

    text = normalize_text(value)
    if not text:
        return "", ""

    parts = text.split(maxsplit=1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    return first_name, last_name


def _int_from_record(
    record: Mapping[str, Any],
    key: str,
    default: int,
) -> int:
    """Return an integer record value with a fallback."""

    try:
        return int(record.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _float_from_record(
    record: Mapping[str, Any],
    key: str,
    default: float,
) -> float:
    """Return a float record value with a fallback."""

    try:
        return float(record.get(key, default) or default)
    except (TypeError, ValueError):
        return default
