"""Read-only detail panel for one person."""

from datetime import date

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QTextEdit

from keep_in_touch.domain.display import (
    contact_age_text,
    contact_method_label,
    date_text,
    display_name,
    middle_name,
    social_lines,
    tags_text,
)
from keep_in_touch.domain.models import Interaction, Person

PANEL_WIDTH = 72
LABEL_WIDTH = 19


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
            _field("Email", person.email),
            _field("Phone", person.phone),
            _field("Relationship", person.relationship),
            _field(
                "Preferred contact",
                contact_method_label(person.preferred_contact_method),
            ),
            _field("Tags", tags_text(person)),
            "",
            _section("Social Handles"),
            *_social_handle_lines(person),
            "",
            _section("Contact History"),
            _field("Days since", contact_age_text(person, date.today())),
            _field("Last contacted", date_text(person.last_contacted_at)),
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
            lines.append(_empty("No interactions logged yet."))

        for interaction in interactions:
            lines.extend(
                [
                    "",
                    _subsection(
                        f"{interaction.date.isoformat()} - "
                        f"{interaction.interaction_type or 'interaction'}"
                    ),
                    _field("Summary", interaction.summary),
                    _field("Follow-up", interaction.follow_up_notes),
                ]
            )

        self.setPlainText("\n".join(lines))


def _title(text: str) -> str:
    """Return an ASCII title block."""

    border = "+" + "=" * PANEL_WIDTH + "+"
    return "\n".join([border, _boxed_line(text.upper()), border])


def _section(text: str) -> str:
    """Return a prominent ASCII section heading."""

    border = "+" + "-" * PANEL_WIDTH + "+"
    return "\n".join([border, _boxed_line(text), border])


def _subsection(text: str) -> str:
    """Return a compact subsection heading."""

    return f"  [{text}]"


def _field(label: str, value: object) -> str:
    """Return an aligned label/value row."""

    text = str(value).strip() if value is not None else ""
    return f"  {label.upper().ljust(LABEL_WIDTH)} | {text or '-'}"


def _block(text: str) -> str:
    """Return indented multi-line body text."""

    stripped = text.strip()
    if not stripped:
        return _empty()
    return "\n".join(f"  {line}" if line else "  " for line in stripped.splitlines())


def _social_handle_lines(person: Person) -> list[str]:
    """Return formatted social handle rows."""

    handles = social_lines(person)
    if not handles:
        return [_empty()]
    return [_field(label, value) for label, value in handles]


def _empty(text: str = "-") -> str:
    """Return a standard empty-state row."""

    return f"  {text}"


def _boxed_line(text: str) -> str:
    """Return text padded inside a fixed-width ASCII box."""

    return f"| {text.ljust(PANEL_WIDTH - 2)} |"
