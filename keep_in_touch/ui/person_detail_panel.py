"""Read-only detail panel for one person."""

from datetime import date

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QTextEdit

from keep_in_touch.domain.display import (
    birthday_text,
    contact_age_text,
    contact_method_label,
    date_text,
    display_name,
    middle_name,
    social_lines,
    tags_text,
)
from keep_in_touch.domain.models import Interaction, Person

LABEL_WIDTH = 19
PANEL_WIDTH = 72


class PersonDetailPanel(QTextEdit):
    """Display selectable, copy-friendly person details."""

    def __init__(self) -> None:
        """Create a read-only text panel styled to fit the Qt application."""

        super().__init__()
        self.setReadOnly(True)
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.setPlaceholderText("Select a person to see details.")
        self.setStyleSheet(
            "QTextEdit {"
            "background: palette(base);"
            "border: 1px solid palette(mid);"
            "border-radius: 6px;"
            "color: palette(text);"
            "padding: 16px;"
            "selection-background-color: palette(highlight);"
            "selection-color: palette(highlighted-text);"
            "}"
        )

    def clear_person(self) -> None:
        """Clear the detail panel."""

        self.setPlainText("")

    def set_person(self, person: Person, interactions: list[Interaction]) -> None:
        """Render a person and their interaction history."""

        self.setPlainText(person_detail_text(person, interactions))


def person_detail_text(person: Person, interactions: list[Interaction]) -> str:
    """Return the copy-friendly text shown in the detail panel."""

    name = display_name(person)
    lines = [
        _title(name),
        "",
        _section("Identity"),
        _field("User ID", person.id),
        _field("First name", person.first_name),
        _field("Middle name", middle_name(person)),
        _field("Last name", person.last_name),
        _field("Nickname", person.nickname),
        _field("Birthday", birthday_text(person, date.today())),
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
        lines.extend(["", *_interaction_block(interaction)])

    return "\n".join(lines)


def _title(text: str) -> str:
    """Return a text title block."""

    return "\n".join(
        [
            _border("╔", "═", "╗"),
            _boxed_line(text.upper()),
            _border("╚", "═", "╝"),
        ]
    )


def _section(text: str) -> str:
    """Return a prominent text section heading."""

    return "\n".join(
        [
            _border("┌", "─", "┐"),
            _boxed_line(text),
            _border("└", "─", "┘"),
        ]
    )


def _interaction_block(interaction: Interaction) -> list[str]:
    """Return an indented readable block for one interaction."""

    title = (
        f"{interaction.date.isoformat()} - "
        f"{interaction.interaction_type or 'interaction'}"
    )
    return [
        f"  ── {title}",
        f"     id   │ {interaction.id}",
        "     summary",
        *_note_lines(interaction.summary, indent="       "),
        "",
        "     follow-up",
        *_note_lines(interaction.follow_up_notes, indent="       "),
    ]


def _field(label: str, value: object) -> str:
    """Return an aligned label/value row."""

    text = str(value).strip() if value is not None else ""
    return f"  {label.ljust(LABEL_WIDTH)} │ {text or '-'}"


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
    """Return text padded inside a fixed-width box."""

    clipped = text[: PANEL_WIDTH - 2]
    return f"│ {clipped.ljust(PANEL_WIDTH - 2)} │"


def _border(left: str, fill: str, right: str) -> str:
    """Return a fixed-width box border."""

    return left + fill * PANEL_WIDTH + right


def _note_lines(text: str, indent: str) -> list[str]:
    """Return readable note lines for interaction summary fields."""

    stripped = text.strip()
    if not stripped:
        return [f"{indent}-"]
    return [
        f"{indent}{line}" if line else indent.rstrip()
        for line in stripped.splitlines()
    ]
