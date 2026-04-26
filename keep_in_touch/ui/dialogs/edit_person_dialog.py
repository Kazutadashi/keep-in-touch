"""Dialog for creating or editing a person."""

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from keep_in_touch.domain.date_utils import today_local
from keep_in_touch.domain.display import social_lines
from keep_in_touch.domain.models import (
    PREFERRED_CONTACT_METHOD_OPTIONS,
    Person,
    RELATIONSHIP_OPTIONS,
)
from keep_in_touch.domain.validation import (
    normalize_relationship,
    normalize_socials,
    normalize_tags,
)
from keep_in_touch.services.interaction_service import InteractionService
from keep_in_touch.ui.dialogs.edit_interactions_dialog import EditInteractionsDialog
from keep_in_touch.ui.dialogs.edit_socials_dialog import EditSocialsDialog

NULL_DATE = QDate(1900, 1, 1)


class EditPersonDialog(QDialog):
    """Collect person information from the user.

    Example:
        dialog = EditPersonDialog()
        if dialog.exec():
            person = dialog.to_person()
    """

    def __init__(
        self,
        person: Person | None = None,
        interaction_service: InteractionService | None = None,
    ) -> None:
        """Create the dialog, optionally prefilled with an existing person."""

        super().__init__()
        self.setWindowTitle("Edit Person" if person else "Add Person")
        self._person = person
        self._interaction_service = interaction_service
        self.socials = normalize_socials(person.socials if person else {})

        self.first_name_edit = QLineEdit(person.first_name if person else "")
        self.middle_name_edit = QLineEdit(person.middle_name if person else "")
        self.last_name_edit = QLineEdit(person.last_name if person else "")
        self.nickname_edit = QLineEdit(person.nickname if person else "")
        self.email_edit = QLineEdit(person.email if person else "")
        self.phone_edit = QLineEdit(person.phone if person else "")

        self.birthday_edit = _optional_date_edit(person.birthday if person else None)

        self.tags_edit = QLineEdit(", ".join(person.tags) if person else "")

        self.relationship_combo = QComboBox()
        self.relationship_combo.setEditable(True)
        self.relationship_combo.addItems(RELATIONSHIP_OPTIONS)
        relationship = person.relationship if person else RELATIONSHIP_OPTIONS[0]
        self.relationship_combo.setCurrentText(normalize_relationship(relationship))

        self.preferred_contact_method_combo = _contact_method_combo(
            person.preferred_contact_method if person else "",
        )
        self.socials_summary_label = QLabel()
        self.socials_summary_label.setWordWrap(True)
        self.edit_socials_button = QPushButton("Edit Social Handles...")
        self.edit_socials_button.clicked.connect(self._edit_socials)
        self._refresh_socials_summary()
        self.edit_interactions_button = QPushButton("Edit Interactions...")
        self.edit_interactions_button.clicked.connect(self._edit_interactions)
        self.edit_interactions_button.setEnabled(
            person is not None and interaction_service is not None,
        )
        last_contacted = person.last_contacted_at if person else None
        self.last_contacted_edit = _optional_date_edit(last_contacted)
        self.bio_edit = QPlainTextEdit(person.bio if person else "")
        self.notes_edit = QPlainTextEdit(person.notes if person else "")

        form = QFormLayout()
        form.addRow("First name *", self.first_name_edit)
        form.addRow("Middle name", self.middle_name_edit)
        form.addRow("Last name", self.last_name_edit)
        form.addRow("Nickname", self.nickname_edit)
        form.addRow("Email", self.email_edit)
        form.addRow("Phone", self.phone_edit)
        form.addRow("Birthday (YYYY-MM-DD)", self.birthday_edit)
        form.addRow("Tags", self.tags_edit)
        form.addRow("Relationship", self.relationship_combo)
        form.addRow(
            "Preferred contact method",
            self.preferred_contact_method_combo,
        )
        form.addRow("Social handles", self._create_socials_row())
        form.addRow("Last contacted (YYYY-MM-DD)", self.last_contacted_edit)
        form.addRow("Interactions", self.edit_interactions_button)
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

        super().accept()

    def to_person(self) -> Person:
        """Return dialog values as a Person."""

        existing = self._person
        return Person(
            id=existing.id if existing else "",
            first_name=self.first_name_edit.text().strip(),
            middle_name=self.middle_name_edit.text().strip(),
            last_name=self.last_name_edit.text().strip(),
            nickname=self.nickname_edit.text().strip(),
            email=self.email_edit.text().strip(),
            phone=self.phone_edit.text().strip(),
            birthday=_date_from_optional_edit(self.birthday_edit),
            tags=normalize_tags(self.tags_edit.text()),
            relationship=normalize_relationship(self.relationship_combo.currentText()),
            preferred_contact_method=_contact_method_from_combo(
                self.preferred_contact_method_combo,
            ),
            socials=normalize_socials(self.socials),
            contact_interval_days=existing.contact_interval_days if existing else 30,
            last_contacted_at=_date_from_optional_edit(self.last_contacted_edit),
            bio=self.bio_edit.toPlainText().strip(),
            notes=self.notes_edit.toPlainText().strip(),
            schema_version=existing.schema_version if existing else 1,
            formula_version=existing.formula_version if existing else 1,
            created_at=existing.created_at if existing else None,
            updated_at=existing.updated_at if existing else None,
            extra_fields=dict(existing.extra_fields) if existing else {},
        )

    def _create_socials_row(self) -> QWidget:
        """Create the compact social handles row for the main form."""

        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.socials_summary_label, stretch=1)
        layout.addWidget(self.edit_socials_button)
        return row

    def _edit_socials(self) -> None:
        """Open the dedicated social handles dialog."""

        dialog = EditSocialsDialog(self.socials)
        if dialog.exec():
            self.socials = dialog.socials()
            self._refresh_socials_summary()

    def _edit_interactions(self) -> None:
        """Open the dedicated interaction history dialog."""

        if self._person is None or self._interaction_service is None:
            QMessageBox.information(
                self,
                "Save person first",
                "Save this person before editing interactions.",
            )
            return

        dialog = EditInteractionsDialog(self._person, self._interaction_service)
        dialog.exec()
        self._refresh_person_after_interaction_edits()

    def _refresh_person_after_interaction_edits(self) -> None:
        """Refresh fields that interactions can change while this dialog is open."""

        if self._person is None or self._interaction_service is None:
            return

        updated_person = self._interaction_service.people_service.get_person(
            self._person.id,
            today=today_local(),
        )
        if updated_person is None:
            return

        self._person = updated_person
        self.last_contacted_edit.setDate(
            _qdate_from_date(updated_person.last_contacted_at),
        )

    def _refresh_socials_summary(self) -> None:
        """Update the compact social handles summary."""

        preview_person = Person(id="", first_name="", socials=self.socials)
        handles = social_lines(preview_person)
        if not handles:
            self.socials_summary_label.setText("No handles saved")
            return

        handle_count = len(handles)
        visible_labels = ", ".join(label for label, _value in handles[:3])
        if handle_count > 3:
            visible_labels = f"{visible_labels} +{handle_count - 3} more"
        self.socials_summary_label.setText(visible_labels)


def _optional_date_edit(value: date | None) -> QDateEdit:
    """Create a nullable date editor using the minimum date as the empty value."""

    edit = QDateEdit(_qdate_from_date(value))
    edit.setMinimumDate(NULL_DATE)
    edit.setMaximumDate(QDate.currentDate())
    edit.setSpecialValueText("Not set")
    edit.setCalendarPopup(True)
    edit.setDisplayFormat("yyyy-MM-dd")
    return edit


def _contact_method_combo(current_value: str) -> QComboBox:
    """Create the searchable preferred contact method selector."""

    combo = QComboBox()
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    combo.addItem("Not set", "")
    for key, label in PREFERRED_CONTACT_METHOD_OPTIONS:
        combo.addItem(label, key)

    current_index = _contact_method_index(combo, current_value)
    if current_index >= 0:
        combo.setCurrentIndex(current_index)
    elif current_value.strip():
        combo.addItem(current_value.strip(), current_value.strip())
        combo.setCurrentIndex(combo.count() - 1)

    completer = combo.completer()
    if completer is not None:
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

    return combo


def _contact_method_index(combo: QComboBox, value: str) -> int:
    """Return the matching combo index for a stored key, label, or unique prefix."""

    clean_value = value.strip().casefold()
    if not clean_value:
        return 0

    prefix_matches: list[int] = []
    for index in range(combo.count()):
        item_key = str(combo.itemData(index) or "").casefold()
        item_label = combo.itemText(index).casefold()
        if clean_value in {item_key, item_label}:
            return index
        if item_key.startswith(clean_value) or item_label.startswith(clean_value):
            prefix_matches.append(index)

    if len(prefix_matches) == 1:
        return prefix_matches[0]
    return -1


def _contact_method_from_combo(combo: QComboBox) -> str:
    """Return the stored key for the selected or typed contact method."""

    typed_text = combo.currentText().strip()
    match_index = _contact_method_index(combo, typed_text)
    if match_index >= 0:
        matched_key = combo.itemData(match_index)
        return str(matched_key or "").strip()

    selected_key = combo.currentData()
    if isinstance(selected_key, str):
        return selected_key.strip()
    return typed_text


def _qdate_from_date(value: date | None) -> QDate:
    """Convert a Python date to QDate, or return the empty sentinel."""

    if value is None:
        return NULL_DATE
    return QDate(value.year, value.month, value.day)


def _date_from_optional_edit(edit: QDateEdit) -> date | None:
    """Return a Python date from a nullable date editor."""

    qdate = edit.date()
    if qdate == NULL_DATE:
        return None
    return date(qdate.year(), qdate.month(), qdate.day())
