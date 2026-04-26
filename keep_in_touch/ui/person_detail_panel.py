"""Read-only detail panel for one person."""

from PySide6.QtWidgets import QTextEdit

from keep_in_touch.domain.models import Interaction, Person


class PersonDetailPanel(QTextEdit):
    """Display person details and interaction history.

    Example:
        panel = PersonDetailPanel()
        panel.clear_person()
    """

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setPlaceholderText("Select a person to see details.")

    def clear_person(self) -> None:
        """Clear the detail panel."""

        self.setPlainText("")

    def set_person(self, person: Person, interactions: list[Interaction]) -> None:
        """Render a person and their interaction history."""

        display_name = person.full_name
        lines = [
            display_name,
            "=" * len(display_name),
            "",
            f"First name: {person.first_name or '-'}",
            f"Last name: {person.last_name or '-'}",
            f"Nickname: {person.nickname or '-'}",
            f"Birthday: {person.birthday.isoformat() if person.birthday else '-'}",
            f"Relationship: {person.relationship or '-'}",
            f"Preferred method: {person.preferred_contact_method or '-'}",
            f"Contact interval: {person.contact_interval_days} days",
            f"Last contacted: {person.last_contacted_at.isoformat() if person.last_contacted_at else '-'}",
            f"Next contact: {person.next_contact_at.isoformat() if person.next_contact_at else 'Not set'}",
            f"Urgency score: {person.urgency_score:g}",
            f"Tags: {', '.join(person.tags) if person.tags else '-'}",
            "",
            "Bio",
            "---",
            person.bio or "-",
            "",
            "Notes",
            "-----",
            person.notes or "-",
            "",
            "Interaction history",
            "-------------------",
        ]

        if not interactions:
            lines.append("No interactions logged yet.")

        for interaction in interactions:
            lines.extend(
                [
                    "",
                    f"{interaction.date.isoformat()} — {interaction.interaction_type or 'interaction'}",
                    f"Summary: {interaction.summary or '-'}",
                    f"Follow-up: {interaction.follow_up_notes or '-'}",
                ]
            )

        self.setPlainText("\n".join(lines))
