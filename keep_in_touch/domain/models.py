"""Plain Python domain models.

These dataclasses are deliberately independent of PySide6 and file storage. That
makes them easy to test and reuse.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


RELATIONSHIP_OPTIONS = [
    "Friend",
    "Family",
    "Classmate",
    "Coworker",
    "Professional",
    "Neighbor",
    "Acquaintance",
    "Other",
]
"""Default relationship categories shown in the user interface.

The app still stores relationships as plain text so users can add new categories
later without requiring a schema change.
"""


SOCIAL_PLATFORMS = [
    ("discord", "Discord"),
    ("matrix", "Matrix"),
    ("linkedin", "LinkedIn"),
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("x", "X / Twitter"),
    ("bluesky", "Bluesky"),
    ("mastodon", "Mastodon"),
    ("github", "GitHub"),
    ("reddit", "Reddit"),
    ("telegram", "Telegram"),
    ("signal", "Signal"),
    ("whatsapp", "WhatsApp"),
    ("website", "Website"),
]
"""Known social/contact platforms shown in the user interface.

The stored data remains a dictionary so additional platforms can be preserved
without requiring a schema migration.
"""


@dataclass
class Person:
    """Represents one person in the relationship tracker.

    Unknown fields from older/newer app versions are preserved in `extra_fields`.

    Example:
        person = Person(
            id="p_001",
            first_name="Jane",
            last_name="Doe",
            contact_interval_days=30,
            relationship="Friend",
        )
        assert person.full_name == "Jane Doe"
    """

    id: str
    first_name: str
    last_name: str = ""
    nickname: str = ""
    bio: str = ""
    birthday: date | None = None
    tags: list[str] = field(default_factory=list)
    relationship: str = "Friend"
    preferred_contact_method: str = ""
    socials: dict[str, str] = field(default_factory=dict)
    contact_interval_days: int = 30
    last_contacted_at: date | None = None
    next_contact_at: date | None = None
    urgency_score: float = 0.0
    notes: str = ""
    schema_version: int = 1
    formula_version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
    extra_fields: dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        """Return a display-friendly full name.

        Example:
            person = Person(id="p_001", first_name="Jane", last_name="Doe")
            assert person.full_name == "Jane Doe"
        """

        parts = [self.first_name.strip(), self.last_name.strip()]
        return " ".join(part for part in parts if part) or "(Unnamed)"

    @property
    def sort_name(self) -> str:
        """Return a stable name value for sorting.

        Example:
            person = Person(id="p_001", first_name="Jane", last_name="Doe")
            assert person.sort_name == "doe, jane"
        """

        if self.last_name.strip():
            return f"{self.last_name.strip()}, {self.first_name.strip()}".lower()
        return self.first_name.strip().lower()


@dataclass
class Interaction:
    """Represents a single interaction with a person.

    Example:
        interaction = Interaction(
            id="i_001",
            person_id="p_001",
            date=date(2026, 4, 26),
            interaction_type="call",
            summary="Caught up about work.",
        )
        assert interaction.person_id == "p_001"
    """

    id: str
    person_id: str
    date: date
    interaction_type: str = ""
    summary: str = ""
    follow_up_notes: str = ""
    schema_version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
    extra_fields: dict[str, Any] = field(default_factory=dict)
