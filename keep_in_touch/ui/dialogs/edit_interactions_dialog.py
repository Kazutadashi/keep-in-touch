"""Dialog for managing a person's interaction history."""

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from keep_in_touch.domain.date_utils import today_local
from keep_in_touch.domain.display import display_name
from keep_in_touch.domain.models import Interaction, Person
from keep_in_touch.services.interaction_service import InteractionService
from keep_in_touch.ui.dialogs.log_interaction_dialog import LogInteractionDialog

INTERACTION_ID_ROLE = Qt.ItemDataRole.UserRole + 1


class EditInteractionsDialog(QDialog):
    """Let the user add, edit, or delete interactions for one person."""

    def __init__(
        self,
        person: Person,
        interaction_service: InteractionService,
    ) -> None:
        """Create the dialog for one person's interaction history."""

        super().__init__()
        self.person = person
        self.interaction_service = interaction_service
        self.interactions: list[Interaction] = []

        self.setWindowTitle(f"Edit Interactions - {display_name(person)}")
        self.resize(760, 420)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Date", "Type", "Summary", "Follow-up"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self._edit_selected_interaction)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._add_interaction)
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self._edit_selected_interaction)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self._delete_selected_interaction)

        actions = QHBoxLayout()
        actions.addWidget(self.add_button)
        actions.addWidget(self.edit_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)

        close_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(actions)
        layout.addWidget(close_buttons)
        self.setLayout(layout)

        self._refresh()

    def _refresh(self) -> None:
        """Reload interactions and refresh the table."""

        self.interactions = self.interaction_service.list_for_person(self.person.id)
        self.table.setRowCount(0)
        for interaction in self.interactions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, value in enumerate(_interaction_row(interaction)):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                if column == 0:
                    item.setData(INTERACTION_ID_ROLE, interaction.id)
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()

    def _add_interaction(self) -> None:
        """Open the add-interaction form."""

        dialog = LogInteractionDialog()
        if not dialog.exec():
            return

        values = dialog.values()
        self.interaction_service.log_interaction(
            person_id=self.person.id,
            interaction_date=values["interaction_date"],
            interaction_type=values["interaction_type"],
            summary=values["summary"],
            follow_up_notes=values["follow_up_notes"],
            today=today_local(),
        )
        self._refresh()

    def _edit_selected_interaction(self, *_args: object) -> None:
        """Open the selected interaction for editing."""

        interaction = self._selected_interaction()
        if interaction is None:
            QMessageBox.information(
                self,
                "No interaction selected",
                "Select an interaction first.",
            )
            return

        dialog = LogInteractionDialog(interaction)
        if not dialog.exec():
            return

        values = dialog.values()
        updated = Interaction(
            id=interaction.id,
            person_id=interaction.person_id,
            date=values["interaction_date"],
            interaction_type=values["interaction_type"],
            summary=values["summary"],
            follow_up_notes=values["follow_up_notes"],
            schema_version=interaction.schema_version,
            created_at=interaction.created_at,
            updated_at=interaction.updated_at,
            extra_fields=dict(interaction.extra_fields),
        )
        self.interaction_service.update_interaction(updated, today=today_local())
        self._refresh()

    def _delete_selected_interaction(self) -> None:
        """Delete the selected interaction after confirmation."""

        interaction = self._selected_interaction()
        if interaction is None:
            QMessageBox.information(
                self,
                "No interaction selected",
                "Select an interaction first.",
            )
            return

        response = QMessageBox.question(
            self,
            "Delete interaction",
            "Delete this interaction? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response != QMessageBox.StandardButton.Yes:
            return

        self.interaction_service.delete_interaction(
            interaction.id,
            today=today_local(),
        )
        self._refresh()

    def _selected_interaction(self) -> Interaction | None:
        """Return the selected interaction, if any."""

        selected = self.table.selectedItems()
        if not selected:
            return None

        first_item = self.table.item(selected[0].row(), 0)
        if first_item is None:
            return None

        interaction_id = first_item.data(INTERACTION_ID_ROLE)
        return next(
            (
                interaction
                for interaction in self.interactions
                if interaction.id == interaction_id
            ),
            None,
        )


def _interaction_row(interaction: Interaction) -> list[str]:
    """Return table display values for one interaction."""

    return [
        interaction.date.isoformat(),
        interaction.interaction_type,
        interaction.summary,
        interaction.follow_up_notes,
    ]
