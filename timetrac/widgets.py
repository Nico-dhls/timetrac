"""Reusable custom widgets for TimeTrac."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QCalendarWidget,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import theme


GERMAN_DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
GERMAN_DAYS_FULL = [
    "Montag", "Dienstag", "Mittwoch", "Donnerstag",
    "Freitag", "Samstag", "Sonntag",
]
GERMAN_MONTHS = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


def make_card(parent=None) -> QFrame:
    frame = QFrame(parent)
    frame.setObjectName("card")
    return frame


def make_label(text: str, object_name: str = "", parent=None) -> QLabel:
    label = QLabel(text, parent)
    if object_name:
        label.setObjectName(object_name)
    return label


def make_divider(parent=None) -> QFrame:
    """Create a horizontal divider line."""
    frame = QFrame(parent)
    frame.setObjectName("divider")
    frame.setFrameShape(QFrame.HLine)
    return frame


class DateNavigator(QWidget):
    """Date selector with prev/next/today buttons and calendar popup."""

    date_changed = Signal(object)  # emits date

    def __init__(self, parent=None):
        super().__init__(parent)
        self._date = date.today()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.prev_btn = QPushButton("◀")
        self.prev_btn.setObjectName("navButton")
        self.prev_btn.setFixedWidth(36)
        self.prev_btn.clicked.connect(self._prev_day)
        self.prev_btn.setToolTip("Vorheriger Tag")

        self.date_btn = QPushButton()
        self.date_btn.setObjectName("secondary")
        self.date_btn.setMinimumWidth(200)
        self.date_btn.clicked.connect(self._open_calendar)
        self.date_btn.setToolTip("Kalender öffnen")

        self.next_btn = QPushButton("▶")
        self.next_btn.setObjectName("navButton")
        self.next_btn.setFixedWidth(36)
        self.next_btn.clicked.connect(self._next_day)
        self.next_btn.setToolTip("Nächster Tag")

        self.today_btn = QPushButton("Heute")
        self.today_btn.setObjectName("secondary")
        self.today_btn.setFixedWidth(60)
        self.today_btn.clicked.connect(self._go_today)

        layout.addWidget(self.prev_btn)
        layout.addWidget(self.date_btn, 1)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.today_btn)

        self._update_display()

    @property
    def selected_date(self) -> date:
        return self._date

    @selected_date.setter
    def selected_date(self, value: date):
        if self._date != value:
            self._date = value
            self._update_display()
            self.date_changed.emit(value)

    def _update_display(self):
        d = self._date
        weekday = GERMAN_DAYS_FULL[d.weekday()]
        month = GERMAN_MONTHS[d.month - 1]
        self.date_btn.setText(f"{weekday}, {d.day}. {month} {d.year}")

    def _prev_day(self):
        self.selected_date = self._date - timedelta(days=1)

    def _next_day(self):
        self.selected_date = self._date + timedelta(days=1)

    def _go_today(self):
        self.selected_date = date.today()

    def _open_calendar(self):
        dialog = CalendarDialog(self._date, self)
        if dialog.exec() == QDialog.Accepted:
            self.selected_date = dialog.selected_date


class CalendarDialog(QDialog):
    """Modal calendar date picker."""

    def __init__(self, current_date: date, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Datum wählen")
        self.setFixedSize(350, 320)
        self.selected_date = current_date

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.cal = QCalendarWidget()
        self.cal.setSelectedDate(QDate(current_date.year, current_date.month, current_date.day))
        self.cal.setGridVisible(True)
        self.cal.setFirstDayOfWeek(Qt.Monday)
        self.cal.activated.connect(self._on_activated)

        layout.addWidget(self.cal)

    def _on_activated(self, qdate: QDate):
        self.selected_date = date(qdate.year(), qdate.month(), qdate.day())
        self.accept()


class TimeEdit(QWidget):
    """Time input with quick-select buttons for common times."""

    time_changed = Signal(str)

    def __init__(self, placeholder: str = "HH:MM", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setMaximumWidth(80)
        self.line_edit.textChanged.connect(self.time_changed.emit)

        self.now_btn = QPushButton("Jetzt")
        self.now_btn.setObjectName("flat")
        self.now_btn.setFixedWidth(40)
        self.now_btn.clicked.connect(self._set_now)
        self.now_btn.setToolTip("Aktuelle Uhrzeit eintragen")

        self.pick_btn = QPushButton("⏱")
        self.pick_btn.setObjectName("flat")
        self.pick_btn.setFixedWidth(28)
        self.pick_btn.clicked.connect(self._open_picker)
        self.pick_btn.setToolTip("Zeit auswählen")

        layout.addWidget(self.line_edit)
        layout.addWidget(self.now_btn)
        layout.addWidget(self.pick_btn)

    @property
    def text(self) -> str:
        return self.line_edit.text().strip()

    @text.setter
    def text(self, value: str):
        self.line_edit.setText(value)

    def _set_now(self):
        self.line_edit.setText(datetime.now().strftime("%H:%M"))

    def _open_picker(self):
        dialog = TimePickerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.line_edit.setText(dialog.selected_time)


class TimePickerDialog(QDialog):
    """Quick time selector grid."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zeit wählen")
        self.setFixedSize(300, 400)
        self.selected_time = ""

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        grid = QVBoxLayout(container)
        grid.setSpacing(2)

        now = datetime.now()
        current_str = now.strftime("%H:%M")

        # Generate slots in 15-minute increments
        slots = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 15, 30, 45)]

        for slot in slots:
            btn = QPushButton(slot)
            btn.setFixedHeight(30)
            if slot == current_str[:5]:  # highlight closest
                btn.setStyleSheet(
                    f"background-color: {theme.ACCENT}; color: white; font-weight: bold;"
                )
            else:
                btn.setObjectName("secondary")
            btn.clicked.connect(lambda checked, t=slot: self._select(t))
            grid.addWidget(btn)

        scroll.setWidget(container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(scroll)

        # Try to scroll to current time area
        # Will be processed after dialog is shown

    def _select(self, time_str: str):
        self.selected_time = time_str
        self.accept()


class EditableComboBox(QComboBox):
    """Editable combobox with recent values."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    @property
    def text(self) -> str:
        return self.currentText().strip()

    @text.setter
    def text(self, value: str):
        self.setCurrentText(value)

    def set_items(self, items: list[str]):
        current = self.currentText()
        self.clear()
        self.addItems(items)
        self.setCurrentText(current)
