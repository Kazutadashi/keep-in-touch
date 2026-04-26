"""Read-only detail panel for one person."""

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QTextEdit

from keep_in_touch.domain.display import (
    contact_status,
    date_text,
    display_name,
    middle_name,
    tags_text,
)
from keep_in_touch.domain.models import Interaction, Person


class PersonDetailPanel(QTextEdit):
    """Display person details and interaction history.

    Example:
        panel = PersonDetailPanel()
        panel.clear_person()
    """

    def __init__(self) -> None:
        """Create a read-only monospace text panel."""

        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.setPlaceholderText("Select a person to see details.")

    def clear_person(self) -> None:
        """Clear the detail panel."""

        self.setPlainText("")

    def set_person(self, person: Person, interactions: list[Interaction]) -> None:
        """Render a person and their interaction history."""

        name = display_name(person)
        lines = [
            _title(name),
            "",
            _section("Identity"),
            _field("First name", person.first_name),
            _field("Middle name", middle_name(person)),
            _field("Last name", person.last_name),
            _field("Nickname", person.nickname),
            _field("Birthday", date_text(person.birthday)),
            "",
            _section("Connection"),
            _field("Relationship", person.relationship),
            _field("Preferred method", person.preferred_contact_method),
            _field("Tags", tags_text(person)),
            "",
            _section("Contact Rhythm"),
            _field("Status", contact_status(person)),
            _field("Interval", f"{person.contact_interval_days} days"),
            _field("Last contacted", date_text(person.last_contacted_at)),
            _field("Next contact", date_text(person.next_contact_at, "Not set")),
            _field("Urgency score", f"{person.urgency_score:g}"),
            "",
            _section("Bio"),
            _block(person.bio),
            "",
            _section("Notes"),
            _block(person.notes),
            "",
            _section("Interaction History"),
        ]

        if not interactions:
            lines.append("  No interactions logged yet.")

        for interaction in interactions:
            lines.extend(
                [
                    "",
                    f"  [{interaction.date.isoformat()}] "
                    f"{interaction.interaction_type or 'interaction'}",
                    _field("Summary", interaction.summary, indent="    "),
                    _field("Follow-up", interaction.follow_up_notes, indent="    "),
                ]
            )

        self.setPlainText("\n".join(lines))


def _title(text: str) -> str:
    """Return an ASCII title block."""

    width = max(40, len(text) + 4)
    border = "+" + "-" * width + "+"
    return "\n".join([border, f"| {text.ljust(width - 2)} |", border])


def _section(text: str) -> str:
    """Return a compact ASCII section heading."""

    return f"-- {text} " + "-" * max(0, 48 - len(text))


def _field(label: str, value: object, indent: str = "  ") -> str:
    """Return an aligned label/value row."""

    text = str(value).strip() if value is not None else ""
    return f"{indent}{label.ljust(17)}: {text or '-'}"


def _block(text: str) -> str:
    """Return indented multi-line body text."""

    stripped = text.strip()
    if not stripped:
        return "  -"
    return "\n".join(f"  {line}" if line else "" for line in stripped.splitlines())
