"""Main application window.

This module owns the top-level PySide6 window layout only. The window delegates
application workflows to services and keeps business logic out of the UI layer.
"""

from datetime import date
from pathlib import Path

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from keep_in_touch import __author__, __version__
from keep_in_touch.app.app_config import AppConfig
from keep_in_touch.domain.date_utils import parse_date, today_local
from keep_in_touch.domain.display import (
    contact_age_text,
    contact_method_label,
    date_text,
    display_name,
    social_lines,
    tags_text,
)
from keep_in_touch.domain.models import Interaction, Person
from keep_in_touch.domain.person_filters import PeopleFilterCriteria, filter_people
from keep_in_touch.services.import_export_service import ImportExportService
from keep_in_touch.services.interaction_service import InteractionService
from keep_in_touch.services.people_service import PeopleService
from keep_in_touch.storage.app_paths import ensure_data_layout
from keep_in_touch.storage.app_settings import save_remembered_data_dir
from keep_in_touch.storage.jsonl_store import JsonlStore
from keep_in_touch.ui.app_icon import app_icon
from keep_in_touch.ui.dialogs.edit_person_dialog import EditPersonDialog
from keep_in_touch.ui.dialogs.log_interaction_dialog import LogInteractionDialog
from keep_in_touch.ui.people_table import PERSON_ID_ROLE, PeopleTable
from keep_in_touch.ui.person_detail_panel import PersonDetailPanel

NO_DATA_FOLDER_MESSAGE = (
    "No data folder selected.\n\n"
    "Use File > Set Data Folder... to choose where Keep in Touch should store "
    "your local data files."
)


class MainWindow(QMainWindow):
    """Main application window.

    The window can open without a configured data folder. In that state, data
    actions are disabled until the user chooses or creates a folder from the File
    menu.

    Example:
        window = MainWindow(AppConfig())
        window.show()
    """

    def __init__(self, config: AppConfig) -> None:
        """Create the main window for a runtime app configuration."""

        super().__init__()
        self.config = config
        self.setWindowTitle("Keep in Touch")
        self.setWindowIcon(app_icon())
        self.setMinimumSize(980, 640)

        self.people_service: PeopleService | None = None
        self.interaction_service: InteractionService | None = None
        self.import_export_service: ImportExportService | None = None

        self.people_table = PeopleTable()
        self.detail_panel = PersonDetailPanel()
        self.people: list[Person] = []
        self.filtered_people: list[Person] = []
        self.data_folder_label = QLabel()
        self.people_count_label = QLabel()

        self._create_actions()
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()
        self._connect_signals()

        self._configure_services_from_config()
        self.refresh_people()

    def preferred_initial_size(self) -> QSize:
        """Return a startup size that shows current table columns before scrolling."""

        detail_width = 680
        outer_margin_width = 20
        splitter_handle_width = 8
        width = (
            self.people_table.preferred_width()
            + detail_width
            + outer_margin_width
            + splitter_handle_width
        )
        return QSize(width, 720)

    def _create_actions(self) -> None:
        """Create reusable menu and context-menu actions."""

        self.set_data_folder_action = QAction("Set Data Folder...", self)
        self.set_data_folder_action.triggered.connect(self.set_data_folder)

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

        self.clear_filters_action = QAction("Clear Filters", self)
        self.clear_filters_action.setShortcut("Ctrl+Shift+F")
        self.clear_filters_action.triggered.connect(self.clear_filters)

        self.import_people_action = QAction("Import People...", self)
        self.import_people_action.triggered.connect(self.import_people)

        self.export_people_action = QAction("Export People...", self)
        self.export_people_action.triggered.connect(self.export_people)

        self.export_interactions_action = QAction("Export Interactions...", self)
        self.export_interactions_action.triggered.connect(self.export_interactions)

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
        file_menu.addAction(self.set_data_folder_action)
        file_menu.addSeparator()
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
        view_menu.addAction(self.clear_filters_action)

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
        splitter.addWidget(self._create_detail_panel())
        splitter.setSizes([self.people_table.preferred_width(), 680])
        central_layout.addWidget(splitter)

        self.setCentralWidget(central_widget)

    def _create_people_panel(self) -> QWidget:
        """Create the left-side people list and action button area."""

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(8)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        title = QLabel("People")
        title.setObjectName("peopleListTitle")
        title_row.addWidget(title)

        self.people_count_label.setObjectName("peopleCountLabel")
        self.people_count_label.setText("(0 shown)")
        self.people_count_label.setStyleSheet("color: palette(window-text);")
        title_row.addWidget(self.people_count_label)
        title_row.addStretch(1)
        layout.addLayout(title_row)
        layout.addWidget(self._create_filter_panel())
        layout.addWidget(self.people_table)
        layout.addWidget(self._create_action_buttons())

        return panel

    def _create_detail_panel(self) -> QWidget:
        """Create the right-side detail panel with a matching title row."""

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(8)

        self.detail_title_label = QLabel("Details")
        self.detail_title_label.setObjectName("detailTitle")
        self.detail_title_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.detail_title_label)
        layout.addWidget(self.detail_panel)

        return panel

    def _create_filter_panel(self) -> QWidget:
        """Create controls for narrowing the people table."""

        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.search_filter_edit = QLineEdit()
        self.search_filter_edit.setPlaceholderText("Search name, tags, notes, email")
        layout.addWidget(QLabel("Search"))
        layout.addWidget(self.search_filter_edit, stretch=1)

        self.last_contact_from_filter_edit = QLineEdit()
        self.last_contact_from_filter_edit.setPlaceholderText("YYYY-MM-DD")
        self.last_contact_from_filter_edit.setMaximumWidth(110)
        layout.addWidget(QLabel("Last contact from"))
        layout.addWidget(self.last_contact_from_filter_edit)

        self.last_contact_to_filter_edit = QLineEdit()
        self.last_contact_to_filter_edit.setPlaceholderText("YYYY-MM-DD")
        self.last_contact_to_filter_edit.setMaximumWidth(110)
        layout.addWidget(QLabel("to"))
        layout.addWidget(self.last_contact_to_filter_edit)

        self.birthday_month_filter_combo = QComboBox()
        self.birthday_month_filter_combo.setMaximumWidth(150)
        layout.addWidget(QLabel("Birthday"))
        layout.addWidget(self.birthday_month_filter_combo)

        self.clear_filters_button = QPushButton("Clear Filters")
        self.clear_filters_button.clicked.connect(self.clear_filters)
        layout.addWidget(self.clear_filters_button)

        self._populate_static_filter_options()
        return panel

    def _create_action_buttons(self) -> QWidget:
        """Create record-specific action buttons.

        Rare global actions, such as changing the data folder, live in the File
        menu instead of this button area.
        """

        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

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
        layout.addStretch(1)

        return panel

    def _create_status_bar(self) -> None:
        """Create a small status bar for context, not commands."""

        status_bar = QStatusBar()
        status_bar.addPermanentWidget(self.data_folder_label, stretch=1)
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
        self.search_filter_edit.textChanged.connect(self._apply_people_filters)
        self.last_contact_from_filter_edit.textChanged.connect(
            self._apply_people_filters
        )
        self.last_contact_to_filter_edit.textChanged.connect(self._apply_people_filters)
        self.birthday_month_filter_combo.currentIndexChanged.connect(
            self._apply_people_filters
        )

    def _configure_services_from_config(self) -> None:
        """Create services when a data folder is configured."""

        if not self.config.has_data_dir:
            self.people_service = None
            self.interaction_service = None
            self.import_export_service = None
            return

        self.people_service = PeopleService(JsonlStore(self.config.people_path))
        self.interaction_service = InteractionService(
            JsonlStore(self.config.interactions_path), self.people_service
        )
        self.import_export_service = ImportExportService(
            self.people_service, self.interaction_service
        )

    def set_data_folder(self) -> None:
        """Let the user choose or create the app data folder."""

        selected_directory = QFileDialog.getExistingDirectory(
            self,
            "Choose or Create Keep in Touch Data Folder",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
            | QFileDialog.Option.DontUseNativeDialog,
        )

        if not selected_directory:
            return

        data_dir = Path(selected_directory).expanduser()
        ensure_data_layout(data_dir)
        save_remembered_data_dir(data_dir)

        self.config = AppConfig(data_dir=data_dir)
        self._configure_services_from_config()
        self.refresh_people()

        self.statusBar().showMessage(f"Using data folder: {data_dir}", 5000)

    def refresh_people(self) -> None:
        """Reload people and refresh the table."""

        if not self._has_data_folder():
            self.people = []
            self.filtered_people = []
            self.people_table.set_people([], today=today_local())
            self.detail_panel.setPlainText(NO_DATA_FOLDER_MESSAGE)
            self.data_folder_label.setText("No data folder selected")
            self._update_people_count_label()
            self._update_action_state()
            return

        selected_id = self.people_table.selected_person_id()
        today = today_local()
        self.people = self._people_service().list_people(today=today)
        self.filtered_people = filter_people(self.people, self._filter_criteria())
        self.people_table.set_people(self.filtered_people, today=today)

        self.data_folder_label.setText(f"Data folder: {self.config.require_data_dir()}")

        if selected_id and any(
            person.id == selected_id for person in self.filtered_people
        ):
            self._select_person_by_id(selected_id)
            self._show_person(selected_id)
        else:
            self.detail_panel.clear_person()

        self._update_action_state()
        self._update_people_count_label()
        self.statusBar().showMessage(self._people_count_message(), 3000)

    def add_person(self) -> None:
        """Open the add-person dialog."""

        if not self._require_data_folder():
            return

        dialog = EditPersonDialog()
        if dialog.exec():
            self._people_service().create_person(
                dialog.to_person(),
                today=today_local(),
            )
            self.refresh_people()

    def edit_selected_person(self) -> None:
        """Open the edit dialog for the selected person."""

        if not self._require_data_folder():
            return

        person = self._selected_person()
        if person is None:
            QMessageBox.information(self, "No selection", "Select a person first.")
            return

        self._edit_person(person)

    def log_interaction(self) -> None:
        """Open the log-interaction dialog for the selected person."""

        if not self._require_data_folder():
            return

        person = self._selected_person()
        if person is None:
            QMessageBox.information(self, "No selection", "Select a person first.")
            return

        dialog = LogInteractionDialog()
        if dialog.exec():
            values = dialog.values()
            self._interaction_service().log_interaction(
                person_id=person.id,
                interaction_date=values["interaction_date"],
                interaction_type=values["interaction_type"],
                summary=values["summary"],
                follow_up_notes=values["follow_up_notes"],
                today=today_local(),
            )
            self.refresh_people()
            self._show_person(person.id)

    def quick_log_contact_today(self) -> None:
        """Log a simple contact for the selected person using today's date."""

        if not self._require_data_folder():
            return

        person = self._selected_person()
        if person is None:
            QMessageBox.information(self, "No selection", "Select a person first.")
            return

        today = today_local()
        self._interaction_service().log_interaction(
            person_id=person.id,
            interaction_date=today,
            interaction_type="contact",
            summary="Quick contact logged.",
            follow_up_notes="",
            today=today,
        )
        self.refresh_people()
        self._show_person(person.id)
        self.statusBar().showMessage(
            f"Logged contact with {display_name(person)}.",
            3000,
        )

    def delete_selected_person(self) -> None:
        """Delete the selected person and their interaction history."""

        if not self._require_data_folder():
            return

        person = self._selected_person()
        if person is None:
            QMessageBox.information(self, "No selection", "Select a person first.")
            return

        response = QMessageBox.question(
            self,
            "Delete person",
            (
                f"Delete {display_name(person)} and all interactions associated "
                "with this "
                "person? This cannot be undone."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response != QMessageBox.StandardButton.Yes:
            return

        self._interaction_service().delete_interactions_for_person(person.id)
        self._people_service().delete_person(person.id, today=today_local())
        self.refresh_people()
        self.statusBar().showMessage(f"Deleted {display_name(person)}.", 3000)

    def copy_selected_person_name(self) -> None:
        """Copy the selected person's full name to the clipboard."""

        person = self._selected_person()
        if person is None:
            return

        name = display_name(person)
        QGuiApplication.clipboard().setText(name)
        self.statusBar().showMessage(f"Copied name for {name}.", 3000)

    def copy_selected_person_summary(self) -> None:
        """Copy a plain-text summary of the selected person to the clipboard."""

        person = self._selected_person()
        if person is None:
            return

        summary = self._person_summary(person)
        QGuiApplication.clipboard().setText(summary)
        self.statusBar().showMessage(
            f"Copied summary for {display_name(person)}.",
            3000,
        )

    def clear_selection(self) -> None:
        """Clear the selected person."""

        self.people_table.clear_selection()
        self.detail_panel.clear_person()
        self._update_action_state()

    def clear_filters(self) -> None:
        """Reset people-table filters."""

        self.search_filter_edit.clear()
        self.last_contact_from_filter_edit.clear()
        self.last_contact_to_filter_edit.clear()
        self.birthday_month_filter_combo.setCurrentIndex(0)
        self._apply_people_filters()

    def export_people(self) -> None:
        """Export people to a chosen CSV or JSONL file."""

        if not self._require_data_folder():
            return

        path = self._save_path("people.jsonl")
        if path is None:
            return

        try:
            self._import_export_service().export_people_file(
                path,
                today=today_local(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
            return

        QMessageBox.information(self, "Export complete", f"Saved {path}")

    def export_interactions(self) -> None:
        """Export interactions to a chosen CSV or JSONL file."""

        if not self._require_data_folder():
            return

        path = self._save_path("interactions.jsonl")
        if path is None:
            return

        try:
            self._import_export_service().export_interactions_file(path)
        except ValueError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
            return

        QMessageBox.information(self, "Export complete", f"Saved {path}")

    def import_people(self) -> None:
        """Import people from a supported CSV or JSONL file."""

        if not self._require_data_folder():
            return

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import People",
            str(self.config.exports_dir),
            "People Files (*.jsonl *.csv);;JSONL Files (*.jsonl);;CSV Files (*.csv)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not filename:
            return

        try:
            imported = self._import_export_service().import_people_file(
                Path(filename),
                today=today_local(),
            )
        except ValueError as exc:
            QMessageBox.warning(
                self,
                "Import failed",
                str(exc),
            )
            return

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
                "Keep in Touch is a local-first personal relationship tracking "
                "application. Data is stored as portable text files in a folder "
                "you choose.\n\n"
                f"Version: {__version__}\n"
                f"Author: {__author__}"
            ),
        )

    def _save_path(self, filename: str) -> Path | None:
        """Ask the user for an export path."""

        default_path = self.config.exports_dir / filename
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "Save Export",
            str(default_path),
            "JSONL Files (*.jsonl);;CSV Files (*.csv)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        return Path(selected) if selected else None

    def _selected_person(self) -> Person | None:
        """Return the selected person, if any."""

        selected_id = self.people_table.selected_person_id()
        return self._person_by_id(selected_id) if selected_id else None

    def _person_by_id(self, person_id: str) -> Person | None:
        """Return a person from the current in-memory list by ID."""

        return next((person for person in self.people if person.id == person_id), None)

    def _apply_people_filters(self, *_args: object) -> None:
        """Refresh the people table using the current filter controls."""

        if not hasattr(self, "people_table"):
            return

        selected_id = self.people_table.selected_person_id()
        self.filtered_people = filter_people(self.people, self._filter_criteria())
        self.people_table.set_people(self.filtered_people, today=today_local())

        if selected_id and any(
            person.id == selected_id for person in self.filtered_people
        ):
            self._select_person_by_id(selected_id)
        else:
            if self._has_data_folder():
                self.detail_panel.clear_person()
            else:
                self.detail_panel.setPlainText(NO_DATA_FOLDER_MESSAGE)

        self._update_action_state()
        self._update_people_count_label()
        if self._has_data_folder():
            self.statusBar().showMessage(self._people_count_message(), 3000)

    def _filter_criteria(self) -> PeopleFilterCriteria:
        """Build filter criteria from the current UI controls."""

        birthday_month = self.birthday_month_filter_combo.currentData()

        return PeopleFilterCriteria(
            search_text=self.search_filter_edit.text(),
            last_contacted_from=self._filter_date(
                self.last_contact_from_filter_edit.text()
            ),
            last_contacted_to=self._filter_date(
                self.last_contact_to_filter_edit.text()
            ),
            birthday_month=birthday_month if isinstance(birthday_month, int) else None,
        )

    def _filter_date(self, value: str) -> date | None:
        """Parse a filter date, treating blank or invalid input as unset."""

        return parse_date(value)

    def _populate_static_filter_options(self) -> None:
        """Populate filter options that do not depend on loaded people."""

        self.birthday_month_filter_combo.addItem("Any month", None)
        for month_number, month_name in enumerate(
            [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ],
            start=1,
        ):
            self.birthday_month_filter_combo.addItem(month_name, month_number)

    def _people_count_message(self) -> str:
        """Return the status-bar count text for current filters."""

        if len(self.filtered_people) == len(self.people):
            return f"Loaded {len(self.people)} people."
        return f"Showing {len(self.filtered_people)} of {len(self.people)} people."

    def _update_people_count_label(self) -> None:
        """Update the count beside the people title."""

        if not self.people:
            self.people_count_label.setText("(0 shown)")
        elif len(self.filtered_people) == len(self.people):
            self.people_count_label.setText(f"({len(self.people)} shown)")
        else:
            self.people_count_label.setText(
                f"({len(self.filtered_people)} of {len(self.people)} shown)"
            )

    def _show_person(self, person_id: str) -> None:
        """Display one person's details."""

        if not self._has_data_folder():
            self.detail_panel.clear_person()
            self._update_action_state()
            return

        person = self._person_by_id(person_id)
        if person is None:
            self.detail_panel.clear_person()
            self._update_action_state()
            return

        interactions = self._interaction_service().list_for_person(person_id)
        self.detail_panel.set_person(person, interactions)
        self._update_action_state()

    def _clear_selected_person(self) -> None:
        """Clear the detail panel when no person is selected."""

        if self._has_data_folder():
            self.detail_panel.clear_person()
        else:
            self.detail_panel.setPlainText(NO_DATA_FOLDER_MESSAGE)
        self._update_action_state()

    def _edit_person_by_id(self, person_id: str) -> None:
        """Edit a person by ID.

        This is used for double-click editing from the people table.
        """

        person = self._person_by_id(person_id)
        if person is None:
            return

        self._edit_person(person)

    def _edit_person(self, person: Person) -> None:
        """Open the edit dialog for a specific person."""

        if not self._has_data_folder():
            return

        dialog = EditPersonDialog(person, self._interaction_service())
        if dialog.exec():
            self._people_service().update_person(
                dialog.to_person(),
                today=today_local(),
            )
            self.refresh_people()

    def _show_people_context_menu(self, position: QPoint) -> None:
        """Show a right-click menu for the people table."""

        if not self._has_data_folder():
            menu = QMenu(self)
            menu.addAction(self.set_data_folder_action)
            global_position = self.people_table.viewport().mapToGlobal(position)
            menu.exec(global_position)
            return

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

        interactions = self._interactions_for_summary(person)
        last_interaction = interactions[0] if interactions else None

        lines = [
            f"Name: {display_name(person)}",
            f"ID: {person.id or '-'}",
            f"First name: {person.first_name or '-'}",
            f"Middle name: {person.middle_name or '-'}",
            f"Last name: {person.last_name or '-'}",
            f"Nickname: {person.nickname or '-'}",
            f"Email: {person.email or '-'}",
            f"Phone: {person.phone or '-'}",
            f"Relationship: {person.relationship or '-'}",
            "Preferred contact method: "
            f"{contact_method_label(person.preferred_contact_method)}",
            f"Last contacted: {date_text(person.last_contacted_at)}",
            f"Days since contact: {contact_age_text(person, today_local())}",
            f"Tags: {tags_text(person)}",
            "",
            "Bio:",
            person.bio or "-",
            "",
            "Notes:",
            person.notes or "-",
        ]

        social_handles = social_lines(person)
        if social_handles:
            lines.extend(["", "Social handles:"])
            lines.extend(f"{label}: {value}" for label, value in social_handles)

        if last_interaction is not None:
            lines.extend(_interaction_summary_lines(last_interaction))

        return "\n".join(lines)

    def _interactions_for_summary(self, person: Person) -> list[Interaction]:
        """Return interactions for summary text when the service is available."""

        if self.interaction_service is None:
            return []
        return self.interaction_service.list_for_person(person.id)

    def _select_person_by_id(self, person_id: str) -> None:
        """Restore a table selection by person ID after a refresh."""

        for row in range(self.people_table.rowCount()):
            item = self.people_table.item(row, 0)
            if item is not None and item.data(PERSON_ID_ROLE) == person_id:
                self.people_table.selectRow(row)
                return

    def _has_data_folder(self) -> bool:
        """Return whether the app currently has a selected data folder."""

        return (
            self.config.has_data_dir
            and self.people_service is not None
            and self.interaction_service is not None
            and self.import_export_service is not None
        )

    def _people_service(self) -> PeopleService:
        """Return the configured people service or raise a clear error."""

        if self.people_service is None:
            raise RuntimeError("People service is unavailable without a data folder.")
        return self.people_service

    def _interaction_service(self) -> InteractionService:
        """Return the configured interaction service or raise a clear error."""

        if self.interaction_service is None:
            raise RuntimeError(
                "Interaction service is unavailable without a data folder."
            )
        return self.interaction_service

    def _import_export_service(self) -> ImportExportService:
        """Return the configured import/export service or raise a clear error."""

        if self.import_export_service is None:
            raise RuntimeError(
                "Import/export service is unavailable without a data folder."
            )
        return self.import_export_service

    def _require_data_folder(self) -> bool:
        """Show a message if no data folder is selected."""

        if self._has_data_folder():
            return True

        QMessageBox.information(
            self,
            "No data folder selected",
            (
                "Choose a data folder before adding people or importing data.\n\n"
                "Use File > Set Data Folder... to choose or create one."
            ),
        )
        return False

    def _update_action_state(self) -> None:
        """Enable or disable actions based on app state."""

        has_data_folder = self._has_data_folder()
        has_selection = has_data_folder and self._selected_person() is not None

        for action in (
            self.import_people_action,
            self.export_people_action,
            self.export_interactions_action,
            self.refresh_action,
            self.add_person_action,
            self.clear_filters_action,
        ):
            action.setEnabled(has_data_folder)

        for action in (
            self.edit_selected_action,
            self.log_interaction_action,
            self.quick_contact_today_action,
            self.delete_selected_action,
            self.copy_name_action,
            self.copy_summary_action,
            self.clear_selection_action,
        ):
            action.setEnabled(has_selection)

        self.add_person_button.setEnabled(has_data_folder)
        self.edit_selected_button.setEnabled(has_selection)
        self.log_interaction_button.setEnabled(has_selection)
        self.delete_selected_button.setEnabled(has_selection)
        self.clear_filters_button.setEnabled(has_data_folder)
        for widget in (
            self.search_filter_edit,
            self.last_contact_from_filter_edit,
            self.last_contact_to_filter_edit,
            self.birthday_month_filter_combo,
        ):
            widget.setEnabled(has_data_folder)


def _interaction_summary_lines(interaction: Interaction) -> list[str]:
    """Return copy-friendly lines for the most recent interaction."""

    interaction_type = interaction.interaction_type or "interaction"
    return [
        "",
        "Most recent interaction:",
        f"{interaction.date.isoformat()} - {interaction_type}",
        f"Summary: {interaction.summary or '-'}",
        f"Follow-up: {interaction.follow_up_notes or '-'}",
    ]
