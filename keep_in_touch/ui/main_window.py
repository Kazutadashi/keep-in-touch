"""Main application window.

This module owns the top-level PySide6 window layout only. The window delegates
application workflows to services and keeps business logic out of the UI layer.
"""

from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from keep_in_touch.app.app_config import AppConfig
from keep_in_touch.domain.date_utils import today_local
from keep_in_touch.domain.models import Person
from keep_in_touch.services.import_export_service import ImportExportService
from keep_in_touch.services.interaction_service import InteractionService
from keep_in_touch.services.people_service import PeopleService
from keep_in_touch.storage.jsonl_store import JsonlStore
from keep_in_touch.ui.dialogs.edit_person_dialog import EditPersonDialog
from keep_in_touch.ui.dialogs.log_interaction_dialog import LogInteractionDialog
from keep_in_touch.ui.people_table import PeopleTable
from keep_in_touch.ui.person_detail_panel import PersonDetailPanel


class MainWindow(QMainWindow):
    """Main application window.

    Responsibilities:
        - Arrange major UI panels.
        - Create standard application menus.
        - Connect UI actions to service calls.
        - Refresh visible data after changes.

    This class should not:
        - Parse CSV files directly.
        - Calculate urgency scores.
        - Read or write JSONL records directly.

    Example:
        window = MainWindow(config)
        window.show()
    """

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle("Keep in Touch")
        self.setMinimumSize(980, 640)

        self.people_service = PeopleService(JsonlStore(config.people_path))
        self.interaction_service = InteractionService(
            JsonlStore(config.interactions_path), self.people_service
        )
        self.import_export_service = ImportExportService(
            self.people_service, self.interaction_service
        )

        self.people_table = PeopleTable()
        self.detail_panel = PersonDetailPanel()
        self.people: list[Person] = []

        self._create_actions()
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()
        self._connect_signals()

        self.refresh_people()

    def _create_actions(self) -> None:
        """Create reusable menu and context-menu actions."""

        self.add_person_action = QAction("Add Person", self)
        self.add_person_action.setShortcut(QKeySequence.StandardKey.New)
        self.add_person_action.triggered.connect(self.add_person)

        self.edit_selected_action = QAction("Edit Selected Person", self)
        self.edit_selected_action.setShortcut("Ctrl+E")
        self.edit_selected_action.triggered.connect(self.edit_selected_person)

        self.log_interaction_action = QAction("Log Interaction...", self)
        self.log_interaction_action.setShortcut("Ctrl+L")
        self.log_interaction_action.triggered.connect(self.log_interaction)

        self.quick_contact_today_action = QAction("Quick Log Contact Today", self)
        self.quick_contact_today_action.setShortcut("Ctrl+Shift+L")
        self.quick_contact_today_action.triggered.connect(self.quick_log_contact_today)

        self.delete_selected_action = QAction("Delete Selected Person", self)
        self.delete_selected_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_selected_action.triggered.connect(self.delete_selected_person)

        self.copy_name_action = QAction("Copy Name", self)
        self.copy_name_action.triggered.connect(self.copy_selected_person_name)

        self.copy_summary_action = QAction("Copy Contact Summary", self)
        self.copy_summary_action.triggered.connect(self.copy_selected_person_summary)

        self.clear_selection_action = QAction("Clear Selection", self)
        self.clear_selection_action.setShortcut(QKeySequence.StandardKey.Cancel)
        self.clear_selection_action.triggered.connect(self.clear_selection)

        self.import_people_action = QAction("Import People CSV...", self)
        self.import_people_action.triggered.connect(self.import_people_csv)

        self.export_people_action = QAction("Export People CSV...", self)
        self.export_people_action.triggered.connect(self.export_people_csv)

        self.export_interactions_action = QAction("Export Interactions CSV...", self)
        self.export_interactions_action.triggered.connect(self.export_interactions_csv)

        self.refresh_action = QAction("Refresh", self)
        self.refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        self.refresh_action.triggered.connect(self.refresh_people)

        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)

        self.about_action = QAction("About Keep in Touch", self)
        self.about_action.triggered.connect(self.show_about_dialog)

    def _create_menu_bar(self) -> None:
        """Create a standard File/Edit/View/Help menu bar."""

        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.import_people_action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_people_action)
        file_menu.addAction(self.export_interactions_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self.add_person_action)
        edit_menu.addAction(self.edit_selected_action)
        edit_menu.addAction(self.log_interaction_action)
        edit_menu.addAction(self.quick_contact_today_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.copy_name_action)
        edit_menu.addAction(self.copy_summary_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.clear_selection_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.delete_selected_action)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.refresh_action)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self.about_action)

    def _create_main_layout(self) -> None:
        """Create the main master-detail layout."""

        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(10, 10, 10, 10)
        central_layout.setSpacing(8)

        splitter = QSplitter()
        splitter.addWidget(self._create_people_panel())
        splitter.addWidget(self.detail_panel)
        splitter.setSizes([520, 680])
        central_layout.addWidget(splitter)

        self.setCentralWidget(central_widget)

    def _create_people_panel(self) -> QWidget:
        """Create the left-side people list and action button area."""

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("People")
        title.setObjectName("peopleListTitle")
        layout.addWidget(title)
        layout.addWidget(self.people_table)
        layout.addWidget(self._create_action_buttons())

        return panel

    def _create_action_buttons(self) -> QGroupBox:
        """Create record-specific action buttons."""

        group_box = QGroupBox("Actions")
        layout = QHBoxLayout(group_box)

        self.add_person_button = QPushButton("Add Person")
        self.add_person_button.clicked.connect(self.add_person)
        layout.addWidget(self.add_person_button)

        self.edit_selected_button = QPushButton("Edit Selected")
        self.edit_selected_button.clicked.connect(self.edit_selected_person)
        layout.addWidget(self.edit_selected_button)

        self.log_interaction_button = QPushButton("Log Interaction")
        self.log_interaction_button.clicked.connect(self.log_interaction)
        layout.addWidget(self.log_interaction_button)

        self.delete_selected_button = QPushButton("Delete")
        self.delete_selected_button.clicked.connect(self.delete_selected_person)
        layout.addWidget(self.delete_selected_button)

        return group_box

    def _create_status_bar(self) -> None:
        """Create a small status bar for context, not commands."""

        status_bar = QStatusBar()
        status_bar.addPermanentWidget(
            QLabel(f"Data folder: {self.config.data_dir}"), stretch=1
        )
        self.setStatusBar(status_bar)

    def _connect_signals(self) -> None:
        """Connect widget signals after all actions and buttons exist."""

        self.people_table.person_selected.connect(self._show_person)
        self.people_table.person_double_clicked.connect(self._edit_person_by_id)
        self.people_table.selection_cleared.connect(self._clear_selected_person)
        self.people_table.itemSelectionChanged.connect(self._update_action_state)
        self.people_table.customContextMenuRequested.connect(
            self._show_people_context_menu
        )

    def refresh_people(self) -> None:
        """Reload people and refresh the table."""

        selected_id = self.people_table.selected_person_id()
        today = today_local()
        self.people = self.people_service.list_people(today=today)
        self.people_table.set_people(self.people, today=today)

        if selected_id and any(person.id == selected_id for person in self.people):
            self._select_person_by_id(selected_id)
            self._show_person(selected_id)
        else:
            self.detail_panel.clear_person()

        self._update_action_state()
        self.statusBar().showMessage(f"Loaded {len(self.people)} people.", 3000)

    def add_person(self) -> None:
        """Open the add-person dialog."""

        dialog = EditPersonDialog()
        if dialog.exec():
            self.people_service.create_person(dialog.to_person(), today=today_local())
            self.refresh_people()

    def edit_selected_person(self) -> None:
        """Open the edit dialog for the selected person."""

        person = self._selected_person()
        if person is None:
            QMessageBox.information(self, "No selection", "Select a person first.")
            return
        self._edit_person(person)

    def log_interaction(self) -> None:
        """Open the log-interaction dialog for the selected person."""

        person = self._selected_person()
        if person is None:
            QMessageBox.information(self, "No selection", "Select a person first.")
            return

        dialog = LogInteractionDialog()
        if dialog.exec():
            values = dialog.values()
            self.interaction_service.log_interaction(
                person_id=person.id,
                interaction_date=values["interaction_date"],  # type: ignore[arg-type]
                interaction_type=str(values["interaction_type"]),
                summary=str(values["summary"]),
                follow_up_notes=str(values["follow_up_notes"]),
                today=today_local(),
            )
            self.refresh_people()
            self._show_person(person.id)

    def quick_log_contact_today(self) -> None:
        """Log a simple contact for the selected person using today's date."""

        person = self._selected_person()
        if person is None:
            QMessageBox.information(self, "No selection", "Select a person first.")
            return

        today = today_local()
        self.interaction_service.log_interaction(
            person_id=person.id,
            interaction_date=today,
            interaction_type="contact",
            summary="Quick contact logged.",
            follow_up_notes="",
            today=today,
        )
        self.refresh_people()
        self._show_person(person.id)
        self.statusBar().showMessage(f"Logged contact with {person.full_name}.", 3000)

    def delete_selected_person(self) -> None:
        """Delete the selected person and their interaction history."""

        person = self._selected_person()
        if person is None:
            QMessageBox.information(self, "No selection", "Select a person first.")
            return

        response = QMessageBox.question(
            self,
            "Delete person",
            (
                f"Delete {person.full_name} and all interactions associated with this "
                "person? This cannot be undone."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response != QMessageBox.StandardButton.Yes:
            return

        self.interaction_service.delete_interactions_for_person(person.id)
        self.people_service.delete_person(person.id, today=today_local())
        self.refresh_people()
        self.statusBar().showMessage(f"Deleted {person.full_name}.", 3000)

    def copy_selected_person_name(self) -> None:
        """Copy the selected person's full name to the clipboard."""

        person = self._selected_person()
        if person is None:
            return

        QGuiApplication.clipboard().setText(person.full_name)
        self.statusBar().showMessage(f"Copied name for {person.full_name}.", 3000)

    def copy_selected_person_summary(self) -> None:
        """Copy a plain-text summary of the selected person to the clipboard."""

        person = self._selected_person()
        if person is None:
            return

        summary = self._person_summary(person)
        QGuiApplication.clipboard().setText(summary)
        self.statusBar().showMessage(f"Copied summary for {person.full_name}.", 3000)

    def clear_selection(self) -> None:
        """Clear the selected person."""

        self.people_table.clear_selection()
        self.detail_panel.clear_person()
        self._update_action_state()

    def export_people_csv(self) -> None:
        """Export people CSV to a chosen file."""

        path = self._save_path("people.csv")
        if path is None:
            return
        self.import_export_service.export_people_csv(path, today=today_local())
        QMessageBox.information(self, "Export complete", f"Saved {path}")

    def export_interactions_csv(self) -> None:
        """Export interactions CSV to a chosen file."""

        path = self._save_path("interactions.csv")
        if path is None:
            return
        self.import_export_service.export_interactions_csv(path)
        QMessageBox.information(self, "Export complete", f"Saved {path}")

    def import_people_csv(self) -> None:
        """Import people from CSV."""

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import People CSV",
            str(self.config.exports_dir),
            "CSV Files (*.csv);;All Files (*)",
        )
        if not filename:
            return

        imported = self.import_export_service.import_people_csv(
            Path(filename), today=today_local()
        )
        self.refresh_people()
        QMessageBox.information(
            self,
            "Import complete",
            f"Imported or updated {len(imported)} people.",
        )

    def show_about_dialog(self) -> None:
        """Show basic application information."""

        QMessageBox.about(
            self,
            "About Keep in Touch",
            (
                "Keep in Touch is a local-first personal relationship "
                "tracking application. Data is stored as portable text files."
            ),
        )

    def _save_path(self, filename: str) -> Path | None:
        """Ask the user for an export path."""

        default_path = self.config.exports_dir / filename
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            str(default_path),
            "CSV Files (*.csv);;All Files (*)",
        )
        return Path(selected) if selected else None

    def _selected_person(self) -> Person | None:
        """Return the selected person, if any."""

        selected_id = self.people_table.selected_person_id()
        if selected_id is None:
            return None

        for person in self.people:
            if person.id == selected_id:
                return person

        return None

    def _show_person(self, person_id: str) -> None:
        """Display one person's details."""

        person = next((item for item in self.people if item.id == person_id), None)
        if person is None:
            self.detail_panel.clear_person()
            self._update_action_state()
            return

        interactions = self.interaction_service.list_for_person(person_id)
        self.detail_panel.set_person(person, interactions)
        self._update_action_state()

    def _clear_selected_person(self) -> None:
        """Clear the detail panel when no person is selected."""

        self.detail_panel.clear_person()
        self._update_action_state()

    def _edit_person_by_id(self, person_id: str) -> None:
        """Edit a person by ID.

        This is used for double-click editing from the people table.
        """

        person = next((item for item in self.people if item.id == person_id), None)
        if person is None:
            return

        self._edit_person(person)

    def _edit_person(self, person: Person) -> None:
        """Open the edit dialog for a specific person."""

        dialog = EditPersonDialog(person)
        if dialog.exec():
            self.people_service.update_person(dialog.to_person(), today=today_local())
            self.refresh_people()

    def _show_people_context_menu(self, position: QPoint) -> None:
        """Show a right-click menu for the people table."""

        self.people_table.select_person_at_position(position)
        has_selection = self._selected_person() is not None

        menu = QMenu(self)
        menu.addAction(self.add_person_action)

        if has_selection:
            menu.addSeparator()
            menu.addAction(self.edit_selected_action)
            menu.addAction(self.log_interaction_action)
            menu.addAction(self.quick_contact_today_action)
            menu.addSeparator()
            menu.addAction(self.copy_name_action)
            menu.addAction(self.copy_summary_action)
            menu.addSeparator()
            menu.addAction(self.clear_selection_action)
            menu.addSeparator()
            menu.addAction(self.delete_selected_action)
        else:
            menu.addSeparator()
            menu.addAction(self.refresh_action)

        global_position = self.people_table.viewport().mapToGlobal(position)
        menu.exec(global_position)

    def _person_summary(self, person: Person) -> str:
        """Return a copy-friendly plain-text summary for one person."""

        interactions = self.interaction_service.list_for_person(person.id)
        last_interaction = interactions[0] if interactions else None

        lines = [
            f"Name: {person.full_name}",
            f"First name: {person.first_name or '-'}",
            f"Last name: {person.last_name or '-'}",
            f"Nickname: {person.nickname or '-'}",
            f"Relationship: {person.relationship or '-'}",
            f"Preferred method: {person.preferred_contact_method or '-'}",
            f"Last contacted: {person.last_contacted_at.isoformat() if person.last_contacted_at else '-'}",
            f"Next contact: {person.next_contact_at.isoformat() if person.next_contact_at else 'Not set'}",
            f"Tags: {', '.join(person.tags) if person.tags else '-'}",
            "",
            "Bio:",
            person.bio or "-",
            "",
            "Notes:",
            person.notes or "-",
        ]

        if last_interaction is not None:
            lines.extend(
                [
                    "",
                    "Most recent interaction:",
                    f"{last_interaction.date.isoformat()} — {last_interaction.interaction_type or 'interaction'}",
                    f"Summary: {last_interaction.summary or '-'}",
                    f"Follow-up: {last_interaction.follow_up_notes or '-'}",
                ]
            )

        return "\n".join(lines)

    def _select_person_by_id(self, person_id: str) -> None:
        """Restore a table selection by person ID after a refresh."""

        for row in range(self.people_table.rowCount()):
            item = self.people_table.item(row, 0)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == person_id:
                self.people_table.selectRow(row)
                return

    def _update_action_state(self) -> None:
        """Enable or disable selected-person actions."""

        has_selection = self._selected_person() is not None

        self.edit_selected_action.setEnabled(has_selection)
        self.log_interaction_action.setEnabled(has_selection)
        self.quick_contact_today_action.setEnabled(has_selection)
        self.delete_selected_action.setEnabled(has_selection)
        self.copy_name_action.setEnabled(has_selection)
        self.copy_summary_action.setEnabled(has_selection)
        self.clear_selection_action.setEnabled(has_selection)

        self.edit_selected_button.setEnabled(has_selection)
        self.log_interaction_button.setEnabled(has_selection)
        self.delete_selected_button.setEnabled(has_selection)
