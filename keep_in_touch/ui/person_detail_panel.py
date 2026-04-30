"""Read-only detail panel for one person."""

from dataclasses import dataclass
from datetime import date
from html import escape

from PySide6.QtGui import QColor, QKeyEvent, QKeySequence, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

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
from keep_in_touch.ui.theme import SCROLLBAR_STYLE


@dataclass(frozen=True)
class DetailDocument:
    """Structured detail content rendered as HTML and plain text."""

    title: str
    summary: str
    tags: str
    sections: list["DetailSection"]


@dataclass(frozen=True)
class DetailSection:
    """A named section in the detail panel."""

    title: str
    content: list["DetailContent"]


@dataclass(frozen=True)
class DetailField:
    """One label/value row."""

    label: str
    value: str


@dataclass(frozen=True)
class DetailBlock:
    """One longer free-text block."""

    text: str


@dataclass(frozen=True)
class DetailInteraction:
    """One interaction history entry."""

    title: str
    fields: list[DetailField]


DetailContent = DetailField | DetailBlock | DetailInteraction


@dataclass(frozen=True)
class DetailColors:
    """Theme colors used by the rich text renderer."""

    text: str
    muted: str
    border: str


class PersonDetailPanel(QWidget):
    """Display styled details while preserving plain-text copying."""

    def __init__(self) -> None:
        """Create a detail panel with a copy button and rich text view."""

        super().__init__()
        self._plain_text = ""

        self.copy_button = QPushButton("Copy Details")
        self.copy_button.clicked.connect(self.copy_details)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.addStretch(1)
        button_row.addWidget(self.copy_button)

        self.text_edit = _DetailTextEdit(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addLayout(button_row)
        layout.addWidget(self.text_edit)

        self.clear_person()

    def setPlainText(self, text: str) -> None:
        """Show a plain message for compatibility with QTextEdit callers."""

        self._plain_text = text
        self.text_edit.setPlainText(text)
        self.copy_button.setEnabled(bool(text.strip()))

    def toPlainText(self) -> str:
        """Return the clean plain-text representation."""

        return self._plain_text or self.text_edit.toPlainText()

    def clear_person(self) -> None:
        """Clear the detail panel."""

        self.setPlainText("")

    def set_person(self, person: Person, interactions: list[Interaction]) -> None:
        """Render a person and their interaction history."""

        document = person_detail_document(person, interactions)
        self._plain_text = render_detail_text(document)
        self.text_edit.setHtml(render_detail_html(document))
        self.copy_button.setEnabled(True)

    def copy_details(self) -> None:
        """Copy the current detail text to the clipboard."""

        QApplication.clipboard().setText(self.toPlainText())


class _DetailTextEdit(QTextEdit):
    """Text edit that copies the panel's plain-text representation."""

    def __init__(self, panel: PersonDetailPanel) -> None:
        """Create the read-only detail text view."""

        super().__init__()
        self._panel = panel
        self.setReadOnly(True)
        self.setAcceptRichText(True)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setPlaceholderText("Select a person to see details.")
        self.setStyleSheet(
            "QTextEdit {"
            "background: palette(base);"
            "border: 1px solid palette(mid);"
            "border-radius: 6px;"
            "color: palette(text);"
            "padding: 18px;"
            "selection-background-color: palette(highlight);"
            "selection-color: palette(highlighted-text);"
            "}"
            f"{SCROLLBAR_STYLE}"
        )

    def copy(self) -> None:
        """Copy clean plain text instead of rich text."""

        self._panel.copy_details()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Keep the standard copy shortcut plain-text friendly."""

        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy()
            event.accept()
            return
        super().keyPressEvent(event)


def person_detail_document(
    person: Person,
    interactions: list[Interaction],
) -> DetailDocument:
    """Build the shared detail document for display and copying."""

    return DetailDocument(
        title=display_name(person),
        summary=_summary_line(person),
        tags=tags_text(person, "No tags"),
        sections=[
            DetailSection(
                "Identity",
                [
                    _field("User ID", person.id),
                    _field("First name", person.first_name),
                    _field("Middle name", middle_name(person)),
                    _field("Last name", person.last_name),
                    _field("Nickname", person.nickname),
                    _field("Birthday", birthday_text(person, date.today())),
                ],
            ),
            DetailSection(
                "Connection",
                [
                    _field("Email", person.email),
                    _field("Phone", person.phone),
                    _field("Relationship", person.relationship),
                    _field(
                        "Preferred contact",
                        contact_method_label(person.preferred_contact_method),
                    ),
                    _field("Tags", tags_text(person)),
                ],
            ),
            DetailSection("Social Handles", _social_handle_content(person)),
            DetailSection(
                "Contact History",
                [
                    _field("Days since", contact_age_text(person, date.today())),
                    _field("Last contacted", date_text(person.last_contacted_at)),
                ],
            ),
            DetailSection("Bio", [DetailBlock(person.bio)]),
            DetailSection("Notes", [DetailBlock(person.notes)]),
            DetailSection(
                "Interaction History",
                _interaction_content(interactions),
            ),
        ],
    )


def render_detail_text(document: DetailDocument) -> str:
    """Render a detail document as clean plain text."""

    lines = [
        document.title,
        document.summary,
        f"Tags: {document.tags}",
        "",
    ]

    for section in document.sections:
        lines.extend(_text_section(section))
        lines.append("")

    return "\n".join(lines).rstrip()


def render_detail_html(document: DetailDocument) -> str:
    """Render a detail document as restrained rich text."""

    colors = _detail_colors()
    sections = "".join(_html_section(section) for section in document.sections)
    return (
        "<!doctype html>"
        "<html><head><style>"
        "body { "
        f"color: {colors.text}; "
        "font-family: sans-serif; font-size: 10pt; margin: 0; }"
        "h1 { font-size: 20pt; font-weight: 700; margin: 0 0 4px 0; "
        f"color: {colors.text}; }}"
        f".summary {{ color: {colors.muted}; margin-bottom: 4px; }}"
        ".tags { margin-bottom: 20px; }"
        f".tag-label {{ color: {colors.muted}; }}"
        ".section { margin-top: 20px; }"
        "h2 { font-size: 11pt; font-weight: 700; margin: 0 0 8px 0; "
        f"color: {colors.text}; padding-bottom: 5px; "
        f"border-bottom: 1px solid {colors.border}; }}"
        "table.fields { border-collapse: collapse; margin: 0; }"
        "td { padding: 2px 12px 3px 0; vertical-align: top; }"
        f"td.label {{ color: {colors.muted}; min-width: 128px; }}"
        ".block { white-space: pre-wrap; line-height: 1.35; margin: 0; }"
        f".empty {{ color: {colors.muted}; }}"
        ".interaction { margin: 0 0 16px 0; padding-left: 10px; "
        f"border-left: 3px solid {colors.border}; }}"
        ".interaction-title { font-weight: 700; margin-bottom: 5px; "
        f"color: {colors.text}; }}"
        "</style></head><body>"
        f"<h1>{escape(document.title)}</h1>"
        f"<div class='summary'>{escape(document.summary)}</div>"
        f"<div class='tags'><span class='tag-label'>Tags:</span> "
        f"{escape(document.tags)}</div>"
        f"{sections}"
        "</body></html>"
    )


def person_detail_text(person: Person, interactions: list[Interaction]) -> str:
    """Return the copy-friendly text for one person."""

    return render_detail_text(person_detail_document(person, interactions))


def person_detail_html(person: Person, interactions: list[Interaction]) -> str:
    """Return the rich detail HTML for one person."""

    return render_detail_html(person_detail_document(person, interactions))


def _text_section(section: DetailSection) -> list[str]:
    """Render one section as plain text lines."""

    lines = [section.title, "-" * len(section.title)]
    for content in section.content:
        lines.extend(_text_content(content))
    return lines


def _text_content(content: DetailContent) -> list[str]:
    """Render one content item as plain text lines."""

    if isinstance(content, DetailField):
        return [f"  {content.label}: {content.value or '-'}"]
    if isinstance(content, DetailBlock):
        return _text_block(content.text)
    return _text_interaction(content)


def _text_block(text: str) -> list[str]:
    """Render multiline text as indented plain text."""

    stripped = text.strip()
    if not stripped:
        return ["  -"]
    return [f"  {line}" if line else "  " for line in stripped.splitlines()]


def _text_interaction(interaction: DetailInteraction) -> list[str]:
    """Render one interaction as plain text."""

    lines = [f"  {interaction.title}"]
    lines.extend(
        f"  {field.label}: {field.value or '-'}"
        for field in interaction.fields
    )
    return lines


def _html_section(section: DetailSection) -> str:
    """Render one section as HTML."""

    body = _html_section_content(section.content)
    return (
        "<div class='section'>"
        f"<h2>{escape(section.title)}</h2>"
        f"{body}"
        "</div>"
    )


def _html_section_content(content_items: list[DetailContent]) -> str:
    """Render section content, grouping adjacent fields into one table."""

    parts: list[str] = []
    field_group: list[DetailField] = []
    for content in content_items:
        if isinstance(content, DetailField):
            field_group.append(content)
            continue
        if field_group:
            parts.append(_html_field_table(field_group))
            field_group = []
        parts.append(_html_content(content))

    if field_group:
        parts.append(_html_field_table(field_group))

    return "".join(parts)


def _html_content(content: DetailContent) -> str:
    """Render one content item as HTML."""

    if isinstance(content, DetailField):
        return _html_field_table([content])
    if isinstance(content, DetailBlock):
        return _html_block(content.text)
    return _html_interaction(content)


def _html_field_table(fields: list[DetailField]) -> str:
    """Render field rows as an HTML table."""

    rows = "".join(
        "<tr>"
        f"<td class='label'>{escape(field.label)}</td>"
        f"<td>{escape(field.value or '-')}</td>"
        "</tr>"
        for field in fields
    )
    return f"<table class='fields'>{rows}</table>"


def _html_block(text: str) -> str:
    """Render long text as HTML."""

    stripped = text.strip()
    if not stripped:
        return "<div class='empty'>-</div>"
    return f"<div class='block'>{escape(stripped)}</div>"


def _html_interaction(interaction: DetailInteraction) -> str:
    """Render one interaction as HTML."""

    return (
        "<div class='interaction'>"
        f"<div class='interaction-title'>{escape(interaction.title)}</div>"
        f"{_html_field_table(interaction.fields)}"
        "</div>"
    )


def _field(label: str, value: object) -> DetailField:
    """Create a normalized detail field."""

    text = str(value).strip() if value is not None else ""
    return DetailField(label, text or "-")


def _social_handle_content(person: Person) -> list[DetailContent]:
    """Return social handles as shared detail content."""

    handles = social_lines(person)
    if not handles:
        return [DetailBlock("")]
    return [_field(label, value) for label, value in handles]


def _interaction_content(interactions: list[Interaction]) -> list[DetailContent]:
    """Return interaction history as shared detail content."""

    if not interactions:
        return [DetailBlock("No interactions logged yet.")]
    return [_interaction_detail(interaction) for interaction in interactions]


def _interaction_detail(interaction: Interaction) -> DetailInteraction:
    """Return one interaction as shared detail content."""

    title = (
        f"{interaction.date.isoformat()} - "
        f"{interaction.interaction_type or 'interaction'}"
    )
    return DetailInteraction(
        title=title,
        fields=[
            _field("ID", interaction.id),
            _field("Summary", interaction.summary),
            _field("Follow-up", interaction.follow_up_notes),
        ],
    )


def _summary_line(person: Person) -> str:
    """Return the compact relationship/contact summary."""

    return " | ".join(
        value
        for value in (
            person.relationship or "Relationship unknown",
            f"Last contacted: {date_text(person.last_contacted_at)}",
            f"Days since: {contact_age_text(person, date.today())}",
        )
        if value
    )


def _detail_colors() -> DetailColors:
    """Return readable HTML colors derived from the active Qt palette."""

    text = _palette_color(QPalette.ColorRole.Text)
    base = _palette_color(QPalette.ColorRole.Base)
    mid = _palette_color(QPalette.ColorRole.Mid)
    return DetailColors(
        text=text.name(),
        muted=_mix_color(text, base, 0.32).name(),
        border=_mix_color(mid, text, 0.2).name(),
    )


def _palette_color(role: QPalette.ColorRole) -> QColor:
    """Return a color from the active application palette."""

    application = QApplication.instance()
    if application is not None:
        return application.palette().color(role)
    return QPalette().color(role)


def _mix_color(start: QColor, end: QColor, progress: float) -> QColor:
    """Return a color between two colors."""

    return QColor(
        round(start.red() + (end.red() - start.red()) * progress),
        round(start.green() + (end.green() - start.green()) * progress),
        round(start.blue() + (end.blue() - start.blue()) * progress),
    )
