"""Table widget for the main people list."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QMouseEvent, QPalette
from PySide6.QtWidgets import QApplication, QHeaderView, QTableWidget, QTableWidgetItem

from keep_in_touch.domain.formulas import days_since_contact
from keep_in_touch.domain.display import (
    birthday_text,
    date_text,
    days_since_contact_text,
    days_until_birthday,
    display_name,
    tags_text,
)
from keep_in_touch.domain.models import Person

PERSON_ID_ROLE = Qt.ItemDataRole.UserRole + 1


@dataclass(frozen=True)
class PeopleTableColumn:
    """Display settings and value lookup for one people-table column."""

    header: str
    width: int
    value: Callable[[Person, date], str]
    sort_value: Callable[[Person, date], object]
    decorate: Callable[[QTableWidgetItem, Person, date], None] | None = None


class SortableTableItem(QTableWidgetItem):
    """Table item that sorts by an explicit sort value."""

    def __lt__(self, other: QTableWidgetItem) -> bool:
        """Compare items using their display sort data."""

        left = self.data(Qt.ItemDataRole.UserRole)
        right = other.data(Qt.ItemDataRole.UserRole)
        return left < right


def _name_cell(person: Person, today: date) -> str:
    """Return name column text."""

    return display_name(person)


def _name_sort_value(person: Person, today: date) -> str:
    """Return name sort value."""

    return display_name(person).lower()


def _days_since_contact_cell(person: Person, today: date) -> str:
    """Return days-since-contact column text."""

    return days_since_contact_text(person, today)


def _days_since_contact_sort_value(person: Person, today: date) -> int:
    """Return numeric days-since-contact sort value."""

    days = days_since_contact(person, today)
    return days if days is not None else 10_000_000


def _birthday_cell(person: Person, today: date) -> str:
    """Return birthday column text."""

    return birthday_text(person, today)


def _birthday_sort_value(person: Person, today: date) -> int:
    """Return days until birthday for sorting."""

    days = days_until_birthday(person, today)
    return days if days is not None else 10_000_000


def _decorate_birthday_cell(
    item: QTableWidgetItem,
    person: Person,
    today: date,
) -> None:
    """Decorate birthday cells by proximity to the next birthday."""

    days = days_until_birthday(person, today)
    if days is None:
        return

    if days == 0:
        item.setText("BIRTHDAY TODAY")
        item.setBackground(QBrush(_palette_color(QPalette.ColorRole.Highlight)))
        item.setForeground(QBrush(_palette_color(QPalette.ColorRole.HighlightedText)))
        font = item.font()
        font.setBold(True)
        font.setWeight(QFont.Weight.Bold)
        item.setFont(font)
    else:
        background = _birthday_proximity_color(days)
        item.setBackground(QBrush(background))
        item.setForeground(QBrush(_readable_text_color(background)))

    item.setToolTip(_birthday_tooltip(person, today, days))


def _birthday_proximity_color(days: int) -> QColor:
    """Return a theme-aware highlight shade based on birthday proximity."""

    base_color = _palette_color(QPalette.ColorRole.Base)
    highlight_color = _palette_color(QPalette.ColorRole.Highlight)
    progress = 1.0 - min(days, 180) / 180
    highlight_weight = 0.18 + progress * 0.58
    return _mix_color(base_color, highlight_color, highlight_weight)


def _mix_color(start: QColor, end: QColor, progress: float) -> QColor:
    """Return a color between two colors."""

    red = _interpolate(start.red(), end.red(), progress)
    green = _interpolate(start.green(), end.green(), progress)
    blue = _interpolate(start.blue(), end.blue(), progress)
    return QColor(red, green, blue)


def _interpolate(start: int, end: int, progress: float) -> int:
    """Return an integer between two channel values."""

    return round(start + (end - start) * progress)


def _palette_color(role: QPalette.ColorRole) -> QColor:
    """Return a color from the active application palette."""

    application = QApplication.instance()
    if application is not None:
        return application.palette().color(role)
    return QPalette().color(role)


def _readable_text_color(background: QColor) -> QColor:
    """Return black or white text based on background brightness."""

    luminance = (
        0.2126 * background.red()
        + 0.7152 * background.green()
        + 0.0722 * background.blue()
    )
    return QColor("#111827") if luminance > 150 else QColor("#f9fafb")


def _birthday_tooltip(person: Person, today: date, days: int) -> str:
    """Return helpful birthday hover text."""

    birthday = date_text(person.birthday)
    if days == 0:
        return f"Birthday: {birthday}. Say happy birthday today."
    if days == 1:
        return f"Birthday: {birthday}. Birthday is tomorrow."
    return f"Birthday: {birthday}. Next birthday is in {days} days."


def _relationship_cell(person: Person, today: date) -> str:
    """Return relationship column text."""

    return person.relationship


def _relationship_sort_value(person: Person, today: date) -> str:
    """Return relationship sort value."""

    return person.relationship.lower()


def _tags_cell(person: Person, today: date) -> str:
    """Return tags column text."""

    return tags_text(person, "")


def _tags_sort_value(person: Person, today: date) -> str:
    """Return tags sort value."""

    return tags_text(person, "").lower()


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
        PeopleTableColumn("Name", 210, _name_cell, _name_sort_value),
        PeopleTableColumn(
            "Days Since Contact",
            160,
            _days_since_contact_cell,
            _days_since_contact_sort_value,
        ),
        PeopleTableColumn(
            "Birthday",
            150,
            _birthday_cell,
            _birthday_sort_value,
            _decorate_birthday_cell,
        ),
        PeopleTableColumn(
            "Relationship",
            130,
            _relationship_cell,
            _relationship_sort_value,
        ),
        PeopleTableColumn("Tags", 220, _tags_cell, _tags_sort_value),
    ]
    WIDTH_PADDING = 36

    def __init__(self) -> None:
        """Create the table and configure selection and column behavior."""

        super().__init__(0, len(self.COLUMNS))
        self.setHorizontalHeaderLabels([column.header for column in self.COLUMNS])
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)
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

        sorting_was_enabled = self.isSortingEnabled()
        self.setSortingEnabled(False)
        self.setRowCount(0)
        for person in people:
            row = self.rowCount()
            self.insertRow(row)
            for column, table_column in enumerate(self.COLUMNS):
                cell_text = table_column.value(person, today)
                item = SortableTableItem(cell_text)
                item.setToolTip(cell_text)
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    table_column.sort_value(person, today),
                )
                if table_column.decorate is not None:
                    table_column.decorate(item, person, today)
                if column == 0:
                    item.setData(PERSON_ID_ROLE, person.id)
                self.setItem(row, column, item)
        self.setSortingEnabled(sorting_was_enabled)

    def selected_person_id(self) -> str | None:
        """Return the selected person ID, if any."""

        selected = self.selectedItems()
        if not selected:
            return None

        row = selected[0].row()
        item = self.item(row, 0)
        if item is None:
            return None

        value = item.data(PERSON_ID_ROLE)
        return str(value) if value else None

    def person_id_at_position(self, position: QPoint) -> str | None:
        """Return the person ID at a table position."""

        item = self.itemAt(position)
        if item is None:
            return None

        first_column_item = self.item(item.row(), 0)
        if first_column_item is None:
            return None

        value = first_column_item.data(PERSON_ID_ROLE)
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

        value = first_column_item.data(PERSON_ID_ROLE)
        if value:
            self.person_double_clicked.emit(str(value))
