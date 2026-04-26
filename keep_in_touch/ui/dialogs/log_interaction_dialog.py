"""Dialog for logging an interaction."""

from datetime import date
from typing import TypedDict

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from keep_in_touch.domain.date_utils import parse_date
from keep_in_touch.domain.models import Interaction


class InteractionDialogValues(TypedDict):
    """Validated interaction values collected from the dialog."""

    interaction_date: date
    interaction_type: str
    summary: str
    follow_up_notes: str


class LogInteractionDialog(QDialog):
    """Collect interaction details from the user.

    Example:
        dialog = LogInteractionDialog()
        if dialog.exec():
            data = dialog.values()
    """

    def __init__(self, interaction: Interaction | None = None) -> None:
        """Create an interaction form, optionally prefilled for editing."""

        super().__init__()
        self.setWindowTitle("Edit Interaction" if interaction else "Log Interaction")

        initial_date = interaction.date if interaction else date.today()
        self.date_edit = QLineEdit(initial_date.isoformat())
        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        self.type_combo.addItems(["text", "call", "email", "in-person", "other"])
        if interaction and interaction.interaction_type:
            self.type_combo.setCurrentText(interaction.interaction_type)
        self.summary_edit = QPlainTextEdit(interaction.summary if interaction else "")
        self.follow_up_edit = QPlainTextEdit(
            interaction.follow_up_notes if interaction else "",
        )

        form = QFormLayout()
        form.addRow("Date (YYYY-MM-DD)", self.date_edit)
        form.addRow("Type", self.type_combo)
        form.addRow("Summary", self.summary_edit)
        form.addRow("Follow-up notes", self.follow_up_edit)

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

        if parse_date(self.date_edit.text()) is None:
            QMessageBox.warning(self, "Invalid date", "Date must use YYYY-MM-DD format.")
            return
        super().accept()

    def values(self) -> InteractionDialogValues:
        """Return dialog values."""

        interaction_date = parse_date(self.date_edit.text())
        if interaction_date is None:
            raise ValueError("Invalid interaction date")
        return {
            "interaction_date": interaction_date,
            "interaction_type": self.type_combo.currentText().strip(),
            "summary": self.summary_edit.toPlainText().strip(),
            "follow_up_notes": self.follow_up_edit.toPlainText().strip(),
        }
