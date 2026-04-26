"""Table widget for the main people list."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from keep_in_touch.domain.display import (
    days_since_contact_text,
    display_name,
    tags_text,
)
from keep_in_touch.domain.models import Person


@dataclass(frozen=True)
class PeopleTableColumn:
    """Display settings and value lookup for one people-table column."""

    header: str
    width: int
    value: Callable[[Person, date], str]


def _name_cell(person: Person, today: date) -> str:
    """Return name column text."""

    return display_name(person)


def _days_since_contact_cell(person: Person, today: date) -> str:
    """Return days-since-contact column text."""

    return days_since_contact_text(person, today)


def _relationship_cell(person: Person, today: date) -> str:
    """Return relationship column text."""

    return person.relationship


def _tags_cell(person: Person, today: date) -> str:
    """Return tags column text."""

    return tags_text(person, "")


class PeopleTable(QTableWidget):
    """Display people in a compact sortable table.

    Supported interactions:
        - Click a row to select a person.
        - Click empty table space to clear the selection.
        - Right-click rows or empty table space for a context menu.
        - Double-click a row to edit that person.

    Example:
        table = PeopleTable()
        table.set_people([], date.today())
    """

    person_selected = Signal(str)
    person_double_clicked = Signal(str)
    selection_cleared = Signal()

    COLUMNS: ClassVar[list[PeopleTableColumn]] = [
        PeopleTableColumn("Name", 210, _name_cell),
        PeopleTableColumn("Days Since Contact", 160, _days_since_contact_cell),
        PeopleTableColumn("Relationship", 130, _relationship_cell),
        PeopleTableColumn("Tags", 220, _tags_cell),
    ]
    WIDTH_PADDING = 36

    def __init__(self) -> None:
        """Create the table and configure selection and column behavior."""

        super().__init__(0, len(self.COLUMNS))
        self.setHorizontalHeaderLabels([column.header for column in self.COLUMNS])
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.verticalHeader().setVisible(False)
        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.horizontalHeader().setMinimumSectionSize(70)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for index, column in enumerate(self.COLUMNS):
            self.setColumnWidth(index, column.width)
        self.itemSelectionChanged.connect(self._emit_selection_change)
        self.itemDoubleClicked.connect(self._emit_person_double_clicked)

    def preferred_width(self) -> int:
        """Return the width needed to show the configured columns without scrolling."""

        header_width = sum(
            self.horizontalHeader().sectionSize(index)
            for index in range(self.columnCount())
        )
        return header_width + self.WIDTH_PADDING

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Clear the selection when the user clicks empty table space."""

        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.itemAt(event.position().toPoint()) is None
        ):
            self.clear_selection()
            event.accept()
            return

        super().mousePressEvent(event)

    def clear_selection(self) -> None:
        """Clear the table selection and current item."""

        self.clearSelection()
        self.setCurrentItem(None)
        self.selection_cleared.emit()

    def set_people(self, people: list[Person], today: date) -> None:
        """Replace the table content with a list of people."""

        self.setRowCount(0)
        for person in people:
            row = self.rowCount()
            self.insertRow(row)
            for column, table_column in enumerate(self.COLUMNS):
                cell_text = table_column.value(person, today)
                item = QTableWidgetItem(cell_text)
                item.setToolTip(cell_text)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, person.id)
                self.setItem(row, column, item)

    def selected_person_id(self) -> str | None:
        """Return the selected person ID, if any."""

        selected = self.selectedItems()
        if not selected:
            return None

        row = selected[0].row()
        item = self.item(row, 0)
        if item is None:
            return None

        value = item.data(Qt.ItemDataRole.UserRole)
        return str(value) if value else None

    def person_id_at_position(self, position: QPoint) -> str | None:
        """Return the person ID at a table position."""

        item = self.itemAt(position)
        if item is None:
            return None

        first_column_item = self.item(item.row(), 0)
        if first_column_item is None:
            return None

        value = first_column_item.data(Qt.ItemDataRole.UserRole)
        return str(value) if value else None

    def select_person_at_position(self, position: QPoint) -> str | None:
        """Select the row at a table position and return its person ID."""

        item = self.itemAt(position)
        if item is None:
            self.clear_selection()
            return None

        self.selectRow(item.row())
        return self.selected_person_id()

    def _emit_selection_change(self) -> None:
        """Emit the correct signal after the selection changes."""

        person_id = self.selected_person_id()
        if person_id:
            self.person_selected.emit(person_id)
        else:
            self.selection_cleared.emit()

    def _emit_person_double_clicked(self, item: QTableWidgetItem) -> None:
        """Emit the person ID when a table row is double-clicked."""

        first_column_item = self.item(item.row(), 0)
        if first_column_item is None:
            return

        value = first_column_item.data(Qt.ItemDataRole.UserRole)
        if value:
            self.person_double_clicked.emit(str(value))
