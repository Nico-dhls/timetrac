"""SAP ITP export dialog with description queue for quick pasting."""

from __future__ import annotations

import threading
import time
from datetime import date

from pynput import keyboard
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
    QRadioButton,
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

    # Automation timing (seconds)
    START_DELAY = 3       # Countdown before automation starts
    NAV_DELAY = 0.3       # Delay between navigation keys
    POPUP_DELAY = 0.8     # Wait for popup to open
    PASTE_DELAY = 0.2     # Wait after Ctrl+V paste
    ROW_DELAY = 0.5       # Delay between rows

    # Navigation: tabs needed to reach each day column from first cell after paste
    # SAP ITP skips some fields, so: Mon=3, Tue=4, Wed=5, Thu=6, Fri=7
    DAY_COLUMN_TABS = [3, 4, 5, 6, 7]  # Mon=3, Tue=4, Wed=5, Thu=6, Fri=7

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
        self._automation_running = False
        self._automation_thread = None

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

        # --- Step 2: Description entry ---
        step2_frame = QFrame()
        step2_frame.setObjectName("card")
        step2_layout = QVBoxLayout(step2_frame)
        step2_layout.setContentsMargins(12, 10, 12, 10)

        step2_title = QLabel("Schritt 2:  Kurztext eingeben")
        step2_title.setObjectName("subtitle")
        step2_layout.addWidget(step2_title)

        # Mode selection
        mode_layout = QHBoxLayout()
        self.auto_radio = QRadioButton("Automatisch")
        self.auto_radio.setChecked(True)
        self.auto_radio.setToolTip("Tastatureingaben automatisch an SAP senden")
        self.manual_radio = QRadioButton("Manuell (Zwischenablage)")
        self.manual_radio.setToolTip("Beschreibungen einzeln in die Zwischenablage legen")
        mode_layout.addWidget(self.auto_radio)
        mode_layout.addWidget(self.manual_radio)
        mode_layout.addStretch()
        step2_layout.addLayout(mode_layout)

        # Status and buttons
        btn_layout = QHBoxLayout()
        self.desc_status = QLabel("Nach dem Kopieren: SAP fokussieren, dann 'Start'")
        self.desc_status.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 12px;")
        btn_layout.addWidget(self.desc_status, 1)

        self.start_auto_btn = QPushButton("Start")
        self.start_auto_btn.setMinimumHeight(36)
        self.start_auto_btn.clicked.connect(self._start_automation)
        btn_layout.addWidget(self.start_auto_btn)

        self.stop_btn = QPushButton("Stopp")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setMinimumHeight(36)
        self.stop_btn.clicked.connect(self._stop_automation)
        self.stop_btn.setVisible(False)
        btn_layout.addWidget(self.stop_btn)

        # Manual mode controls (hidden by default)
        self.start_queue_btn = QPushButton("Start")
        self.start_queue_btn.setObjectName("secondary")
        self.start_queue_btn.setMinimumHeight(36)
        self.start_queue_btn.clicked.connect(self._start_description_queue)
        self.start_queue_btn.setVisible(False)
        btn_layout.addWidget(self.start_queue_btn)

        self.next_desc_btn = QPushButton("Nächste ▶")
        self.next_desc_btn.setMinimumHeight(36)
        self.next_desc_btn.clicked.connect(self._next_description)
        self.next_desc_btn.setVisible(False)
        self.next_desc_btn.setToolTip("Nächste Kurzbeschreibung in Zwischenablage laden")
        btn_layout.addWidget(self.next_desc_btn)

        step2_layout.addLayout(btn_layout)

        # Preview label for manual mode
        self.desc_preview = QLabel("")
        self.desc_preview.setObjectName("notesHint")
        self.desc_preview.setVisible(False)
        step2_layout.addWidget(self.desc_preview)

        layout.addWidget(step2_frame)

        # Connect mode radio buttons
        self.auto_radio.toggled.connect(self._update_mode_ui)

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

    def _update_mode_ui(self):
        """Toggle UI between automatic and manual mode."""
        auto_mode = self.auto_radio.isChecked()

        # Show/hide automation buttons
        self.start_auto_btn.setVisible(auto_mode)
        self.stop_btn.setVisible(False)  # Always hidden initially

        # Show/hide manual buttons
        self.start_queue_btn.setVisible(not auto_mode)
        self.next_desc_btn.setVisible(False)  # Only visible after starting

        # Reset status text
        if auto_mode:
            self.desc_status.setText("Nach dem Kopieren: SAP fokussieren, dann 'Start'")
            self.desc_status.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 12px;")
        else:
            self.desc_status.setText("Klicke \"Start\" → dann in SAP jeden Zeitslot doppelklicken → Ctrl+V")
            self.desc_status.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 12px;")

        self.desc_preview.setVisible(False)

    # --- Step 2: Automatic keyboard automation ---

    def _start_automation(self):
        """Start keyboard automation for description entry."""
        # Build description queue
        self._desc_queue = []
        for row_idx in range(len(self._rows)):
            desc = self.table.item(row_idx, 2).text().strip()
            self._desc_queue.append(desc)

        if not self._desc_queue:
            self.desc_status.setText("Keine Einträge vorhanden.")
            return

        self._automation_running = True
        self._desc_index = 0

        # Update UI
        self.start_auto_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.copy_grid_btn.setEnabled(False)
        self.auto_radio.setEnabled(False)
        self.manual_radio.setEnabled(False)

        # Start automation in background thread
        self._automation_thread = threading.Thread(target=self._run_automation, daemon=True)
        self._automation_thread.start()

    def _stop_automation(self):
        """Stop the automation."""
        self._automation_running = False
        self._finish_automation()

    def _finish_automation(self):
        """Reset UI after automation completes or is stopped."""
        # Must run on main thread
        QTimer.singleShot(0, self._reset_automation_ui)

    def _reset_automation_ui(self):
        """Reset automation UI state."""
        self.start_auto_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.copy_grid_btn.setEnabled(True)
        self.auto_radio.setEnabled(True)
        self.manual_radio.setEnabled(True)

        if self._desc_index >= len(self._desc_queue):
            self.desc_status.setText("Alle Kurztexte eingetragen!")
            self.desc_status.setStyleSheet(f"color: {theme.SUCCESS}; font-size: 12px; font-weight: bold;")
        else:
            self.desc_status.setText(f"Gestoppt bei Eintrag {self._desc_index + 1}/{len(self._desc_queue)}")
            self.desc_status.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 12px;")

    def _run_automation(self):
        """Execute the keyboard automation sequence (runs in background thread)."""
        keyboard_controller = keyboard.Controller()
        weekday_index = self._selected_date.weekday()

        # Calculate tabs needed to reach day column
        if 0 <= weekday_index < 5:
            tabs_to_day = self.DAY_COLUMN_TABS[weekday_index]
        else:
            return  # Weekend, no entries

        try:
            # Countdown before starting
            for i in range(self.START_DELAY, 0, -1):
                if not self._automation_running:
                    return
                QTimer.singleShot(0, lambda secs=i: self.desc_status.setText(
                    f"Start in {secs} Sekunden... (SAP fokussieren!)"
                ))
                time.sleep(1)

            if not self._automation_running:
                return

            # Navigate to day column (from first row, column 0)
            for _ in range(tabs_to_day):
                if not self._automation_running:
                    return
                keyboard_controller.press(keyboard.Key.tab)
                keyboard_controller.release(keyboard.Key.tab)
                time.sleep(self.NAV_DELAY)

            # Process each row
            for idx, desc in enumerate(self._desc_queue):
                if not self._automation_running:
                    return

                self._desc_index = idx
                # Update status on main thread
                QTimer.singleShot(0, lambda i=idx, d=desc: self._update_automation_status(i, d))

                # F2 to open popup
                keyboard_controller.press(keyboard.Key.f2)
                keyboard_controller.release(keyboard.Key.f2)
                time.sleep(self.POPUP_DELAY)

                if not self._automation_running:
                    return

                # Tab to reach Kurztext field (skip hours field)
                keyboard_controller.press(keyboard.Key.tab)
                keyboard_controller.release(keyboard.Key.tab)
                time.sleep(self.NAV_DELAY)

                if not self._automation_running:
                    return

                # Type description directly
                if desc:
                    keyboard_controller.type(desc)
                    time.sleep(self.PASTE_DELAY)

                if not self._automation_running:
                    return

                # Enter to confirm
                keyboard_controller.press(keyboard.Key.enter)
                keyboard_controller.release(keyboard.Key.enter)
                time.sleep(self.ROW_DELAY)

                if not self._automation_running:
                    return

                # Move to next row (down arrow)
                if idx < len(self._desc_queue) - 1:
                    keyboard_controller.press(keyboard.Key.down)
                    keyboard_controller.release(keyboard.Key.down)
                    time.sleep(self.NAV_DELAY)

            # Done
            self._desc_index = len(self._desc_queue)
            self._finish_automation()

        except Exception as e:
            QTimer.singleShot(0, lambda: self._show_automation_error(str(e)))
            self._finish_automation()

    def _update_automation_status(self, index: int, desc: str):
        """Update status label during automation (called on main thread)."""
        total = len(self._desc_queue)
        psp = self._rows[index]["psp"] if index < len(self._rows) else ""
        self.desc_status.setText(
            f"Eintrag {index + 1}/{total}: {psp} - {desc[:30]}{'...' if len(desc) > 30 else ''}"
        )
        self.desc_status.setStyleSheet(f"color: {theme.ACCENT_LIGHT}; font-size: 12px;")

    def _show_automation_error(self, error: str):
        """Show automation error message."""
        self.desc_status.setText(f"Fehler: {error}")
        self.desc_status.setStyleSheet(f"color: {theme.ERROR}; font-size: 12px;")
