"""Dialog for creating or editing a person."""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
)

from keep_in_touch.domain.date_utils import parse_date
from keep_in_touch.domain.models import Person, RELATIONSHIP_OPTIONS
from keep_in_touch.domain.validation import normalize_relationship, normalize_tags


class EditPersonDialog(QDialog):
    """Collect person information from the user.

    Example:
        dialog = EditPersonDialog()
        if dialog.exec():
            person = dialog.to_person()
    """

    def __init__(self, person: Person | None = None) -> None:
        """Create the dialog, optionally prefilled with an existing person."""

        super().__init__()
        self.setWindowTitle("Edit Person" if person else "Add Person")
        self._person = person

        self.first_name_edit = QLineEdit(person.first_name if person else "")
        self.last_name_edit = QLineEdit(person.last_name if person else "")
        self.nickname_edit = QLineEdit(person.nickname if person else "")
        self.birthday_edit = QLineEdit(
            person.birthday.isoformat() if person and person.birthday else ""
        )
        self.tags_edit = QLineEdit(", ".join(person.tags) if person else "")

        self.relationship_combo = QComboBox()
        self.relationship_combo.setEditable(True)
        self.relationship_combo.addItems(RELATIONSHIP_OPTIONS)
        relationship = person.relationship if person else RELATIONSHIP_OPTIONS[0]
        self.relationship_combo.setCurrentText(normalize_relationship(relationship))

        self.method_edit = QLineEdit(person.preferred_contact_method if person else "")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3650)
        self.interval_spin.setValue(person.contact_interval_days if person else 30)
        self.last_contacted_edit = QLineEdit(
            person.last_contacted_at.isoformat()
            if person and person.last_contacted_at
            else ""
        )
        self.bio_edit = QPlainTextEdit(person.bio if person else "")
        self.notes_edit = QPlainTextEdit(person.notes if person else "")

        form = QFormLayout()
        form.addRow("First name *", self.first_name_edit)
        form.addRow("Last name", self.last_name_edit)
        form.addRow("Nickname", self.nickname_edit)
        form.addRow("Birthday (YYYY-MM-DD)", self.birthday_edit)
        form.addRow("Tags", self.tags_edit)
        form.addRow("Relationship", self.relationship_combo)
        form.addRow("Preferred method", self.method_edit)
        form.addRow("Contact interval days", self.interval_spin)
        form.addRow("Last contacted (YYYY-MM-DD)", self.last_contacted_edit)
        form.addRow("Bio", self.bio_edit)
        form.addRow("Notes", self.notes_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def accept(self) -> None:
        """Validate before accepting."""

        if not self.first_name_edit.text().strip():
            QMessageBox.warning(self, "Missing first name", "First name is required.")
            return

        invalid_date_label = self._first_invalid_date_label()
        if invalid_date_label is not None:
            QMessageBox.warning(
                self,
                "Invalid date",
                f"{invalid_date_label} must use YYYY-MM-DD format.",
            )
            return

        super().accept()

    def _first_invalid_date_label(self) -> str | None:
        """Return the first date field label with invalid text."""

        for label, value in (
            ("Birthday", self.birthday_edit.text()),
            ("Last contacted", self.last_contacted_edit.text()),
        ):
            if value.strip() and parse_date(value) is None:
                return label
        return None

    def to_person(self) -> Person:
        """Return dialog values as a Person."""

        existing = self._person
        return Person(
            id=existing.id if existing else "",
            first_name=self.first_name_edit.text().strip(),
            last_name=self.last_name_edit.text().strip(),
            nickname=self.nickname_edit.text().strip(),
            birthday=parse_date(self.birthday_edit.text()),
            tags=normalize_tags(self.tags_edit.text()),
            relationship=normalize_relationship(self.relationship_combo.currentText()),
            preferred_contact_method=self.method_edit.text().strip(),
            contact_interval_days=self.interval_spin.value(),
            last_contacted_at=parse_date(self.last_contacted_edit.text()),
            bio=self.bio_edit.toPlainText().strip(),
            notes=self.notes_edit.toPlainText().strip(),
            schema_version=existing.schema_version if existing else 1,
            formula_version=existing.formula_version if existing else 1,
            created_at=existing.created_at if existing else None,
            updated_at=existing.updated_at if existing else None,
            extra_fields=dict(existing.extra_fields) if existing else {},
        )
