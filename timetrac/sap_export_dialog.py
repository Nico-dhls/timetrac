"""SAP ITP export dialog with description queue for quick pasting."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from . import theme
from .database import Database

GERMAN_DAYS_SHORT = ["Mo", "Di", "Mi", "Do", "Fr"]
GERMAN_DAYS_FULL = [
    "Montag", "Dienstag", "Mittwoch", "Donnerstag",
    "Freitag", "Samstag", "Sonntag",
]


class SapExportDialog(QDialog):
    """SAP ITP export with two-step workflow:

    1. Copy grid rows (Leistungsart + PSP + hours) → paste into SAP ITP grid
    2. Start description mode → each Ctrl+V in SAP pastes the next Kurzbeschreibung

    Aggregates entries by PSP + Leistungsart for the selected day.
    Descriptions are editable before copying.
    """

    def __init__(self, db: Database, current_date: date, parent=None):
        super().__init__(parent)
        self.db = db
        self._selected_date = current_date
        self.setWindowTitle("SAP ITP Export")
        self.setMinimumSize(700, 520)
        self.resize(800, 580)

        self._rows: list[dict] = []
        self._desc_queue: list[str] = []
        self._desc_index: int = 0

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header - show selected day
        weekday_name = GERMAN_DAYS_FULL[self._selected_date.weekday()]
        header = QLabel(
            f"{weekday_name}, {self._selected_date.strftime('%d.%m.%Y')}"
        )
        header.setObjectName("subtitle")
        layout.addWidget(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)  # Leistungsart, PSP, Kurzbeschreibung, Stunden
        headers = ["Leistungsart", "PSP", "Kurzbeschreibung", "Stunden"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

        # --- Step 1: Copy grid ---
        step1_frame = QFrame()
        step1_frame.setObjectName("card")
        step1_layout = QHBoxLayout(step1_frame)
        step1_layout.setContentsMargins(12, 10, 12, 10)

        step1_label = QLabel(
            "Schritt 1:  Zeilen kopieren → in SAP ITP einfügen\n"
            "(Leistungsart, PSP und Stunden werden übernommen)"
        )
        step1_label.setObjectName("subtitle")
        step1_layout.addWidget(step1_label, 1)

        self.copy_grid_btn = QPushButton("Zeilen kopieren")
        self.copy_grid_btn.setMinimumHeight(36)
        self.copy_grid_btn.clicked.connect(self._copy_grid)
        step1_layout.addWidget(self.copy_grid_btn)

        layout.addWidget(step1_frame)

        # --- Step 2: Description queue ---
        step2_frame = QFrame()
        step2_frame.setObjectName("card")
        step2_layout = QHBoxLayout(step2_frame)
        step2_layout.setContentsMargins(12, 10, 12, 10)

        step2_text = QVBoxLayout()
        step2_title = QLabel(
            "Schritt 2:  Beschreibungen nacheinander einfügen"
        )
        step2_title.setObjectName("subtitle")
        step2_text.addWidget(step2_title)

        self.desc_status = QLabel(
            "Klicke \"Start\" → dann in SAP jeden Zeitslot doppelklicken → Ctrl+V"
        )
        self.desc_status.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 12px;")
        step2_text.addWidget(self.desc_status)

        self.desc_preview = QLabel("")
        self.desc_preview.setObjectName("notesHint")
        self.desc_preview.setVisible(False)
        step2_text.addWidget(self.desc_preview)

        step2_layout.addLayout(step2_text, 1)

        self.start_queue_btn = QPushButton("Start")
        self.start_queue_btn.setObjectName("secondary")
        self.start_queue_btn.setMinimumHeight(36)
        self.start_queue_btn.clicked.connect(self._start_description_queue)
        step2_layout.addWidget(self.start_queue_btn)

        self.next_desc_btn = QPushButton("Nächste ▶")
        self.next_desc_btn.setMinimumHeight(36)
        self.next_desc_btn.clicked.connect(self._next_description)
        self.next_desc_btn.setVisible(False)
        self.next_desc_btn.setToolTip("Nächste Kurzbeschreibung in Zwischenablage laden")
        step2_layout.addWidget(self.next_desc_btn)

        layout.addWidget(step2_frame)

        # Close
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Schließen")
        close_btn.setObjectName("secondary")
        close_btn.clicked.connect(self.reject)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

    def _load_data(self):
        entries = self.db.get_entries_for_date(self._selected_date)

        # Aggregate by (psp, activity_type) — merge descriptions
        aggregated: dict[tuple[str, str], dict] = {}
        for entry in entries:
            key = (entry.psp, entry.activity_type)
            if key not in aggregated:
                aggregated[key] = {
                    "psp": entry.psp,
                    "activity_type": entry.activity_type,
                    "descriptions": [],
                    "hours": 0.0,
                }
            row = aggregated[key]
            row["hours"] += entry.hours
            if entry.description and entry.description not in row["descriptions"]:
                row["descriptions"].append(entry.description)

        self._rows = list(aggregated.values())

        # Look up preset notes for description hints
        presets = self.db.get_presets()
        preset_notes: dict[str, str] = {}
        for p in presets:
            if p.psp and p.notes:
                preset_notes[p.psp] = p.notes

        self.table.setRowCount(len(self._rows) + 1)  # +1 for totals

        grand_total = 0.0

        for row_idx, row in enumerate(self._rows):
            # Leistungsart (read-only)
            act_item = QTableWidgetItem(row["activity_type"])
            act_item.setFlags(act_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 0, act_item)

            # PSP (read-only)
            psp_item = QTableWidgetItem(row["psp"])
            psp_item.setFlags(psp_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 1, psp_item)

            # Kurzbeschreibung (editable)
            desc_text = "; ".join(row["descriptions"])
            hint = preset_notes.get(row["psp"], "")
            desc_item = QTableWidgetItem(desc_text)
            if hint:
                desc_item.setToolTip(f"Format-Hinweis: {hint}")
            self.table.setItem(row_idx, 2, desc_item)

            # Hours (read-only)
            h = row["hours"]
            grand_total += h
            h_item = QTableWidgetItem(f"{h:.2f}".replace(".", ",") if h > 0 else "")
            h_item.setFlags(h_item.flags() & ~Qt.ItemIsEditable)
            h_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 3, h_item)

        # Totals row
        total_row = len(self._rows)
        for col in (0, 1):
            empty = QTableWidgetItem("")
            empty.setFlags(empty.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(total_row, col, empty)

        sum_label = QTableWidgetItem("Summe")
        sum_label.setFlags(sum_label.flags() & ~Qt.ItemIsEditable)
        font = sum_label.font()
        font.setBold(True)
        sum_label.setFont(font)
        self.table.setItem(total_row, 2, sum_label)

        gt_item = QTableWidgetItem(f"{grand_total:.2f}".replace(".", ","))
        gt_item.setFlags(gt_item.flags() & ~Qt.ItemIsEditable)
        gt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        f = gt_item.font()
        f.setBold(True)
        gt_item.setFont(f)
        self.table.setItem(total_row, 3, gt_item)

    # --- Step 1: Copy grid rows ---

    def _copy_grid(self):
        lines = []
        weekday_index = self._selected_date.weekday()

        for row_idx in range(len(self._rows)):
            act_type = self.table.item(row_idx, 0).text()
            psp = self.table.item(row_idx, 1).text()
            hours = self.table.item(row_idx, 3).text() if self.table.item(row_idx, 3) else ""

            # Build day columns (Mo-Fr), only fill the selected day
            day_cols = [""] * 5
            if 0 <= weekday_index < 5 and hours:
                day_cols[weekday_index] = hours

            # SAP GUI ITP: Leistungsart | PSP | Bezeichnung | Bezeichnung | StatKz | ME | Summe | Mo-Fr
            # Leave Bezeichnung empty — SAP requires entering it via detail popup
            row = [act_type, psp, "", "", "", "", ""] + day_cols
            lines.append("\t".join(row))

        text = "\r\n".join(lines) + "\r\n"
        QApplication.clipboard().setText(text)

        self.copy_grid_btn.setText("Kopiert!")
        self.copy_grid_btn.setObjectName("success")
        self.copy_grid_btn.setStyle(self.copy_grid_btn.style())
        QTimer.singleShot(2000, lambda: self._reset_copy_btn())

    def _reset_copy_btn(self):
        self.copy_grid_btn.setText("Zeilen kopieren")
        self.copy_grid_btn.setObjectName("")
        self.copy_grid_btn.setStyle(self.copy_grid_btn.style())

    # --- Step 2: Description queue ---

    def _start_description_queue(self):
        """Build queue of descriptions and put first one in clipboard."""
        self._desc_queue = []
        for row_idx in range(len(self._rows)):
            desc = self.table.item(row_idx, 2).text().strip()
            self._desc_queue.append(desc)

        if not any(self._desc_queue):
            self.desc_status.setText("Keine Kurzbeschreibungen vorhanden.")
            return

        self._desc_index = 0
        self._put_current_desc()

        self.start_queue_btn.setVisible(False)
        self.next_desc_btn.setVisible(True)

    def _next_description(self):
        """Advance to next description and put it in clipboard."""
        self._desc_index += 1
        if self._desc_index >= len(self._desc_queue):
            self.desc_status.setText("Alle Kurzbeschreibungen eingefügt!")
            self.desc_status.setStyleSheet(f"color: {theme.SUCCESS}; font-size: 12px; font-weight: bold;")
            self.desc_preview.setVisible(False)
            self.next_desc_btn.setVisible(False)
            self.start_queue_btn.setText("Neu starten")
            self.start_queue_btn.setVisible(True)
            return

        self._put_current_desc()

    def _put_current_desc(self):
        """Put current description in clipboard and update UI."""
        desc = self._desc_queue[self._desc_index]
        row = self._rows[self._desc_index]
        total = len(self._desc_queue)
        current = self._desc_index + 1

        QApplication.clipboard().setText(desc)

        psp_hint = row["psp"]
        self.desc_status.setText(
            f"Beschreibung {current}/{total} in Zwischenablage  —  "
            f"Jetzt in SAP den Zeitslot für \"{psp_hint}\" doppelklicken → Ctrl+V"
        )
        self.desc_status.setStyleSheet(f"color: {theme.ACCENT_LIGHT}; font-size: 12px;")

        if desc:
            self.desc_preview.setText(f"Ctrl+V fügt ein: {desc}")
        else:
            self.desc_preview.setText("(leer — kein Text zum Einfügen)")
        self.desc_preview.setVisible(True)

        # Update button text
        remaining = total - current
        if remaining > 0:
            self.next_desc_btn.setText(f"Nächste ▶  ({remaining} übrig)")
        else:
            self.next_desc_btn.setText("Fertig")
