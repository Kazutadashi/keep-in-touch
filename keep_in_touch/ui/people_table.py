"""Table widget for the main people list."""

from datetime import date

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from keep_in_touch.domain.formulas import days_overdue
from keep_in_touch.domain.models import Person


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

    HEADERS = [
        "First Name",
        "Last Name",
        "Next Contact",
        "Overdue",
        "Relationship",
        "Method",
        "Tags",
    ]

    def __init__(self) -> None:
        super().__init__(0, len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.itemSelectionChanged.connect(self._emit_selection_change)
        self.itemDoubleClicked.connect(self._emit_person_double_clicked)

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
            overdue = days_overdue(person, today)
            values = [
                person.first_name,
                person.last_name,
                person.next_contact_at.isoformat() if person.next_contact_at else "Not set",
                str(overdue) if overdue else "",
                person.relationship,
                person.preferred_contact_method,
                ", ".join(person.tags),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
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
