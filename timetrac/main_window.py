"""Main application window for TimeTrac."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QSize
from PySide6.QtGui import QAction, QBrush, QColor, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .database import Database
from .models import Preset, TimeEntry, TimeMode
from .preset_dialog import PresetManagerDialog
from .sap_export_dialog import SapExportDialog
from .statistics_dialog import StatisticsDialog
from .widgets import DateNavigator, EditableComboBox, TimeEdit, make_card, make_divider, make_label

GERMAN_DAYS_SHORT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
GERMAN_DAYS_FULL = [
    "Montag", "Dienstag", "Mittwoch", "Donnerstag",
    "Freitag", "Samstag", "Sonntag",
]


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("TimeTrac")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        self._editing_entry: TimeEntry | None = None
        self._timer_start: datetime | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_timer_display)
        self._presets: list[Preset] = []

        icon_path = Path(__file__).resolve().parent.parent / "timetable_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build_ui()
        self._refresh_presets()
        self._refresh_data()

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+N"), self, self._reset_form)
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_entry)
        QShortcut(QKeySequence("Ctrl+T"), self, self._toggle_timer)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # === LEFT PANEL: Entry Form ===
        left_panel = self._build_left_panel()
        splitter.addWidget(left_panel)

        # === RIGHT PANEL: Overview ===
        right_panel = self._build_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([520, 780])
        main_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._status_label = QLabel("")
        self.status_bar.addWidget(self._status_label)

    def _build_left_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {theme.BG_PRIMARY}; border: none; }}")

        panel = QFrame()
        panel.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        layout.addWidget(make_label("Zeiterfassung", "title"))
        layout.addWidget(make_label("Erfasse Zeiten für SAP ITP.", "subtitle"))
        layout.addSpacing(4)

        # Date navigator
        self.date_nav = DateNavigator()
        self.date_nav.date_changed.connect(self._on_date_changed)
        layout.addWidget(self.date_nav)

        layout.addWidget(make_divider())

        # Preset selector
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(8)

        preset_layout.addWidget(make_label("Vorlage:", "sectionLabel"))
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(150)
        self.preset_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.preset_combo.currentIndexChanged.connect(self._apply_preset)
        preset_layout.addWidget(self.preset_combo, 1)

        manage_btn = QPushButton("Verwalten")
        manage_btn.setObjectName("secondary")
        manage_btn.clicked.connect(self._open_preset_manager)
        preset_layout.addWidget(manage_btn)

        layout.addLayout(preset_layout)

        # Notes hint (shown when preset has notes)
        self.notes_hint = QLabel("")
        self.notes_hint.setObjectName("notesHint")
        self.notes_hint.setWordWrap(True)
        self.notes_hint.setVisible(False)
        layout.addWidget(self.notes_hint)

        layout.addWidget(make_divider())

        # PSP + Activity type
        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(12)

        psp_col = QVBoxLayout()
        psp_col.setSpacing(4)
        psp_col.addWidget(make_label("PSP", "sectionLabel"))
        self.psp_combo = EditableComboBox()
        self.psp_combo.setPlaceholderText("PSP-Element")
        psp_col.addWidget(self.psp_combo)
        fields_layout.addLayout(psp_col, 1)

        type_col = QVBoxLayout()
        type_col.setSpacing(4)
        type_col.addWidget(make_label("Leistungsart", "sectionLabel"))
        self.type_combo = EditableComboBox()
        self.type_combo.setPlaceholderText("Leistungsart")
        type_col.addWidget(self.type_combo)
        fields_layout.addLayout(type_col, 1)

        layout.addLayout(fields_layout)

        layout.addWidget(make_divider())

        # Time input
        time_header = QHBoxLayout()
        time_header.addWidget(make_label("Zeit", "sectionLabel"))
        time_header.addStretch()

        # Segmented control for mode toggle
        segment_layout = QHBoxLayout()
        segment_layout.setSpacing(0)

        self.duration_seg_btn = QPushButton("Dauer")
        self.duration_seg_btn.setObjectName("segmentLeft")
        self.duration_seg_btn.setCheckable(True)
        self.duration_seg_btn.setChecked(True)
        self.duration_seg_btn.clicked.connect(lambda: self._set_time_mode(TimeMode.DURATION))

        self.range_seg_btn = QPushButton("Zeitspanne")
        self.range_seg_btn.setObjectName("segmentRight")
        self.range_seg_btn.setCheckable(True)
        self.range_seg_btn.setChecked(False)
        self.range_seg_btn.clicked.connect(lambda: self._set_time_mode(TimeMode.RANGE))

        segment_layout.addWidget(self.duration_seg_btn)
        segment_layout.addWidget(self.range_seg_btn)
        time_header.addLayout(segment_layout)

        layout.addLayout(time_header)

        # Range mode
        self.range_widget = QWidget()
        range_layout = QHBoxLayout(self.range_widget)
        range_layout.setContentsMargins(0, 0, 0, 0)
        range_layout.setSpacing(12)

        range_layout.addWidget(QLabel("Start:"))
        self.start_edit = TimeEdit("08:00")
        range_layout.addWidget(self.start_edit)

        range_layout.addWidget(QLabel("Ende:"))
        self.end_edit = TimeEdit("17:00")
        range_layout.addWidget(self.end_edit)

        layout.addWidget(self.range_widget)
        self.range_widget.setVisible(False)

        # Duration mode
        self.duration_widget = QWidget()
        dur_layout = QHBoxLayout(self.duration_widget)
        dur_layout.setContentsMargins(0, 0, 0, 0)

        dur_layout.addWidget(QLabel("Stunden:"))
        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(0.0, 24.0)
        self.hours_spin.setDecimals(2)
        self.hours_spin.setSingleStep(0.25)
        self.hours_spin.setValue(0.0)
        dur_layout.addWidget(self.hours_spin)
        dur_layout.addStretch()

        layout.addWidget(self.duration_widget)
        self.duration_widget.setVisible(True)
        self._time_mode = TimeMode.DURATION

        layout.addWidget(make_divider())

        # Description
        layout.addWidget(make_label("Beschreibung", "sectionLabel"))
        self.desc_combo = EditableComboBox()
        self.desc_combo.setPlaceholderText("Kurzbeschreibung der Tätigkeit")
        layout.addWidget(self.desc_combo)

        layout.addSpacing(8)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.save_btn = QPushButton("Eintrag hinzufügen")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self._save_entry)

        self.update_btn = QPushButton("Aktualisieren")
        self.update_btn.setMinimumHeight(40)
        self.update_btn.clicked.connect(self._save_entry)
        self.update_btn.setVisible(False)

        self.reset_btn = QPushButton("Neu")
        self.reset_btn.setObjectName("secondary")
        self.reset_btn.setMinimumHeight(40)
        self.reset_btn.clicked.connect(self._reset_form)

        self.delete_btn = QPushButton("Löschen")
        self.delete_btn.setObjectName("danger")
        self.delete_btn.setMinimumHeight(40)
        self.delete_btn.clicked.connect(self._delete_entry)

        btn_layout.addWidget(self.save_btn, 2)
        btn_layout.addWidget(self.update_btn, 2)
        btn_layout.addWidget(self.reset_btn, 1)
        btn_layout.addWidget(self.delete_btn, 1)

        layout.addLayout(btn_layout)

        layout.addWidget(make_divider())

        # Timer
        timer_card = make_card()
        timer_layout = QHBoxLayout(timer_card)
        timer_layout.setContentsMargins(16, 14, 16, 14)

        self.timer_btn = QPushButton("Timer starten")
        self.timer_btn.setObjectName("secondary")
        self.timer_btn.setMinimumHeight(36)
        self.timer_btn.clicked.connect(self._toggle_timer)
        timer_layout.addWidget(self.timer_btn)

        self.timer_label = QLabel("")
        self.timer_label.setObjectName("timerDisplay")
        timer_layout.addWidget(self.timer_label, 1, Qt.AlignCenter)

        self.timer_abort_btn = QPushButton("✕")
        self.timer_abort_btn.setObjectName("flat")
        self.timer_abort_btn.setFixedWidth(32)
        self.timer_abort_btn.clicked.connect(self._abort_timer)
        self.timer_abort_btn.setVisible(False)
        timer_layout.addWidget(self.timer_abort_btn)

        layout.addWidget(timer_card)
        layout.addStretch()

        scroll.setWidget(panel)
        return scroll

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 24, 20, 20)
        layout.setSpacing(12)

        # Tab bar with Statistik button on the right
        tab_header = QHBoxLayout()

        self.tabs = QTabWidget()

        stats_btn = QPushButton("Statistik")
        stats_btn.setObjectName("flat")
        stats_btn.setToolTip("Zeitstatistik nach PSP anzeigen")
        stats_btn.clicked.connect(self._open_statistics)
        tab_header.addStretch()
        tab_header.addWidget(stats_btn)
        layout.addLayout(tab_header)

        # --- Day tab ---
        day_widget = QWidget()
        day_layout = QVBoxLayout(day_widget)
        day_layout.setContentsMargins(0, 10, 0, 0)

        self.day_tree = QTreeWidget()
        self.day_tree.setHeaderLabels(["PSP", "Leistungsart", "Beschreibung", "Zeit", "Stunden"])
        self.day_tree.setRootIsDecorated(False)
        self.day_tree.setAlternatingRowColors(True)
        self.day_tree.header().setStretchLastSection(False)
        self.day_tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.day_tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        self.day_tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        self.day_tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.day_tree.header().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.day_tree.setColumnWidth(0, 120)
        self.day_tree.setColumnWidth(1, 120)
        self.day_tree.currentItemChanged.connect(self._on_entry_selected)
        self.day_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        day_layout.addWidget(self.day_tree, 1)

        # Day totals
        day_totals = QFrame()
        day_totals.setObjectName("card")
        totals_layout = QHBoxLayout(day_totals)
        totals_layout.setContentsMargins(16, 12, 16, 12)

        self.day_total_label = QLabel("Summe Tag: 0,00 h")
        self.day_total_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        totals_layout.addWidget(self.day_total_label)

        totals_layout.addStretch()

        self.week_total_label = QLabel("Woche: 0,00 h")
        self.week_total_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {theme.TEXT_SECONDARY};")
        totals_layout.addWidget(self.week_total_label)

        day_layout.addWidget(day_totals)

        # Copy buttons
        copy_layout = QHBoxLayout()
        copy_layout.addStretch()
        self.copy_btn = QPushButton("Eintrag kopieren")
        self.copy_btn.setObjectName("secondary")
        self.copy_btn.setToolTip("Ausgewählten Eintrag im SAP ITP-Format in die Zwischenablage kopieren")
        self.copy_btn.clicked.connect(self._copy_for_sap)
        copy_layout.addWidget(self.copy_btn)

        self.copy_day_btn = QPushButton("Tag kopieren")
        self.copy_day_btn.setObjectName("secondary")
        self.copy_day_btn.setToolTip("Alle Einträge des Tages im SAP ITP-Format kopieren")
        self.copy_day_btn.clicked.connect(self._copy_day_for_sap)
        copy_layout.addWidget(self.copy_day_btn)

        export_day_btn = QPushButton("SAP ITP Export...")
        export_day_btn.setToolTip("Wochenexport mit editierbarer Vorschau öffnen")
        export_day_btn.clicked.connect(self._open_sap_export)
        copy_layout.addWidget(export_day_btn)

        day_layout.addLayout(copy_layout)

        self.tabs.addTab(day_widget, "Tagesansicht")

        # --- Week tab ---
        week_widget = QWidget()
        week_layout = QVBoxLayout(week_widget)
        week_layout.setContentsMargins(0, 10, 0, 0)

        self.week_tree = QTreeWidget()
        self.week_tree.setHeaderLabels(["PSP", "Leistungsart", "Beschreibung", "Mo", "Di", "Mi", "Do", "Fr", "Sa", "So", "Summe"])
        self.week_tree.setRootIsDecorated(False)
        self.week_tree.setAlternatingRowColors(True)
        self.week_tree.header().setStretchLastSection(False)
        self.week_tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.week_tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        self.week_tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        for i in range(3, 11):
            self.week_tree.header().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.week_tree.setColumnWidth(0, 110)
        self.week_tree.setColumnWidth(1, 120)
        week_layout.addWidget(self.week_tree, 1)

        # Week export
        wcopy_layout = QHBoxLayout()
        wcopy_layout.addStretch()
        export_btn = QPushButton("SAP ITP Export...")
        export_btn.setToolTip("Woche als editierbare Vorschau öffnen und für SAP ITP kopieren")
        export_btn.clicked.connect(self._open_sap_export)
        wcopy_layout.addWidget(export_btn)
        week_layout.addLayout(wcopy_layout)

        self.tabs.addTab(week_widget, "Wochenansicht")

        layout.addWidget(self.tabs, 1)

        return panel

    # --- Data & Refresh ---

    def _refresh_data(self):
        self._refresh_day_view()
        self._refresh_week_view()
        self._refresh_combos()
        self._update_totals()

    def _refresh_day_view(self):
        self.day_tree.clear()
        day = self.date_nav.selected_date
        entries = self.db.get_entries_for_date(day)

        # Group by (psp, type, desc)
        groups: dict[tuple, list[TimeEntry]] = {}
        for entry in entries:
            key = (entry.psp, entry.activity_type, entry.description)
            groups.setdefault(key, []).append(entry)

        for (psp, act_type, desc), group_entries in groups.items():
            # Add individual entry rows
            for entry in group_entries:
                time_info = ""
                if entry.start_time and entry.end_time:
                    time_info = f"{entry.start_time}\u2013{entry.end_time}"
                item = QTreeWidgetItem([
                    entry.psp,
                    entry.activity_type,
                    entry.description,
                    time_info if time_info else "\u2013",
                    f"{entry.hours:.2f}",
                ])
                item.setData(0, Qt.UserRole, entry.id)
                self.day_tree.addTopLevelItem(item)

            # Add group summary row only when 2+ entries share the same key
            if len(group_entries) > 1:
                group_hours = sum(e.hours for e in group_entries)
                summary = QTreeWidgetItem([
                    "",
                    "",
                    f"Summe: {desc}",
                    "",
                    f"{group_hours:.2f}",
                ])
                summary.setFlags(summary.flags() & ~Qt.ItemIsSelectable)
                font = summary.font(0)
                font.setBold(True)
                group_brush = QBrush(QColor(theme.GROUP_ROW))
                for col in range(5):
                    summary.setFont(col, font)
                    summary.setBackground(col, group_brush)
                self.day_tree.addTopLevelItem(summary)

    def _refresh_week_view(self):
        self.week_tree.clear()
        day = self.date_nav.selected_date
        week_data = self.db.get_entries_for_week(day)
        start_of_week = day - timedelta(days=day.weekday())

        # Aggregate by (psp, type, desc) across the week
        aggregated: dict[tuple, list[float]] = {}
        for d, entries in sorted(week_data.items()):
            day_index = (d - start_of_week).days
            for entry in entries:
                key = (entry.psp, entry.activity_type, entry.description)
                if key not in aggregated:
                    aggregated[key] = [0.0] * 7
                aggregated[key][day_index] += entry.hours

        for (psp, act_type, desc), daily_hours in aggregated.items():
            total = sum(daily_hours)
            row_data = [psp, act_type, desc]
            for h in daily_hours:
                row_data.append(f"{h:.2f}" if h > 0 else "")
            row_data.append(f"{total:.2f}")
            item = QTreeWidgetItem(row_data)
            # Bold the total
            font = item.font(10)
            font.setBold(True)
            item.setFont(10, font)
            self.week_tree.addTopLevelItem(item)

        # Totals row
        day_totals = [0.0] * 7
        for daily_hours in aggregated.values():
            for i, h in enumerate(daily_hours):
                day_totals[i] += h
        grand_total = sum(day_totals)
        total_row = ["", "", "Summe"]
        for h in day_totals:
            total_row.append(f"{h:.2f}" if h > 0 else "")
        total_row.append(f"{grand_total:.2f}")
        total_item = QTreeWidgetItem(total_row)
        font = total_item.font(0)
        font.setBold(True)
        for col in range(11):
            total_item.setFont(col, font)
        self.week_tree.addTopLevelItem(total_item)

        # Update week header with dates
        for i in range(7):
            d = start_of_week + timedelta(days=i)
            self.week_tree.headerItem().setText(3 + i, f"{GERMAN_DAYS_SHORT[i]}\n{d.day:02d}.{d.month:02d}")

    def _refresh_combos(self):
        self.psp_combo.set_items(self.db.get_recent_values("psp"))
        self.type_combo.set_items(self.db.get_recent_values("activity_type"))
        day = self.date_nav.selected_date
        entries = self.db.get_entries_for_date(day)
        descs = list(dict.fromkeys(e.description for e in entries if e.description))
        self.desc_combo.set_items(descs or self.db.get_recent_values("description"))

    def _refresh_presets(self):
        self._presets = self.db.get_presets()
        self.preset_combo.clear()
        self.preset_combo.addItem("— Keine Vorlage —")
        for preset in self._presets:
            self.preset_combo.addItem(preset.display_name, preset.id)

    def _update_totals(self):
        day = self.date_nav.selected_date
        day_total = self.db.get_day_total(day)
        week_total = self.db.get_week_total(day)
        self.day_total_label.setText(f"Summe Tag: {day_total:.2f} h")
        self.week_total_label.setText(f"Woche: {week_total:.2f} h")

        remaining = 8.0 - day_total
        if remaining > 0 and day_total > 0:
            self._status_label.setText(f"Noch {remaining:.2f} h bis 8 Stunden  |  DB: {self.db.db_path}")
        elif day_total >= 8:
            self._status_label.setText(f"Tagessoll erreicht  |  DB: {self.db.db_path}")
        else:
            self._status_label.setText(f"DB: {self.db.db_path}")

    # --- Event Handlers ---

    def _on_date_changed(self, new_date: date):
        self._editing_entry = None
        self._toggle_edit_mode(False)
        self._refresh_data()

    def _on_entry_selected(self, current, previous):
        if current is None:
            self._editing_entry = None
            self._toggle_edit_mode(False)
            return

        entry_id = current.data(0, Qt.UserRole)
        if entry_id is None:
            self._editing_entry = None
            self._toggle_edit_mode(False)
            return

        entries = self.db.get_entries_for_date(self.date_nav.selected_date)
        entry = next((e for e in entries if e.id == entry_id), None)
        if entry is None:
            return

        self._editing_entry = entry
        self.psp_combo.text = entry.psp
        self.type_combo.text = entry.activity_type
        self.desc_combo.text = entry.description

        if entry.mode == TimeMode.RANGE:
            self._set_time_mode(TimeMode.RANGE)
            self.start_edit.text = entry.start_time
            self.end_edit.text = entry.end_time
        else:
            self._set_time_mode(TimeMode.DURATION)
            self.hours_spin.setValue(entry.hours)

        self._toggle_edit_mode(True)

    def _toggle_edit_mode(self, editing: bool):
        self.update_btn.setVisible(editing)
        self.save_btn.setVisible(not editing)

    def _apply_preset(self, index: int):
        if index <= 0:
            self.notes_hint.setVisible(False)
            return
        preset_id = self.preset_combo.currentData()
        preset = next((p for p in self._presets if p.id == preset_id), None)
        if preset is None:
            self.notes_hint.setVisible(False)
            return

        if preset.psp:
            self.psp_combo.text = preset.psp
        if preset.activity_type:
            self.type_combo.text = preset.activity_type

        if preset.notes:
            self.notes_hint.setText(f"Hinweis: {preset.notes}")
            self.notes_hint.setVisible(True)
        else:
            self.notes_hint.setVisible(False)

    def _set_time_mode(self, mode: TimeMode):
        self._time_mode = mode
        is_range = mode == TimeMode.RANGE
        self.range_widget.setVisible(is_range)
        self.duration_widget.setVisible(not is_range)
        self.range_seg_btn.setChecked(is_range)
        self.duration_seg_btn.setChecked(not is_range)

    # --- CRUD ---

    def _validate_and_build_entry(self) -> TimeEntry | None:
        psp = self.psp_combo.text
        act_type = self.type_combo.text
        desc = self.desc_combo.text
        day = self.date_nav.selected_date

        if not act_type:
            QMessageBox.warning(self, "Eingabe", "Bitte eine Leistungsart angeben.")
            return None

        if self._time_mode == TimeMode.RANGE:
            start = self.start_edit.text
            end = self.end_edit.text
            if not start or not end:
                QMessageBox.warning(self, "Eingabe", "Bitte Start- und Endzeit angeben.")
                return None
            try:
                start_dt = datetime.strptime(start, "%H:%M")
                end_dt = datetime.strptime(end, "%H:%M")
            except ValueError:
                QMessageBox.warning(self, "Eingabe", "Zeitformat muss HH:MM sein.")
                return None
            if end_dt <= start_dt:
                QMessageBox.warning(self, "Eingabe", "Ende muss nach Start liegen.")
                return None
            hours = (end_dt - start_dt).total_seconds() / 3600
        else:
            hours = self.hours_spin.value()
            if hours <= 0:
                QMessageBox.warning(self, "Eingabe", "Stunden müssen größer als 0 sein.")
                return None
            start = ""
            end = ""

        return TimeEntry(
            id=self._editing_entry.id if self._editing_entry else None,
            date=day,
            psp=psp,
            activity_type=act_type,
            description=desc,
            hours=hours,
            start_time=start,
            end_time=end,
            mode=self._time_mode,
        )

    def _save_entry(self):
        entry = self._validate_and_build_entry()
        if entry is None:
            return

        if self._editing_entry:
            self.db.update_entry(entry)
            self._show_status("Eintrag aktualisiert.")
        else:
            self.db.add_entry(entry)
            self._show_status("Eintrag hinzugefügt.")

        self._reset_form()
        self._refresh_data()

    def _delete_entry(self):
        if not self._editing_entry:
            current = self.day_tree.currentItem()
            if not current or current.data(0, Qt.UserRole) is None:
                QMessageBox.information(self, "Löschen", "Bitte einen Eintrag zum Löschen auswählen.")
                return
            entry_id = current.data(0, Qt.UserRole)
        else:
            entry_id = self._editing_entry.id

        reply = QMessageBox.question(
            self, "Löschen", "Eintrag wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.delete_entry(entry_id)
            self._reset_form()
            self._refresh_data()
            self._show_status("Eintrag gelöscht.")

    def _reset_form(self):
        self._editing_entry = None
        self.preset_combo.setCurrentIndex(0)
        self.psp_combo.text = ""
        self.type_combo.text = ""
        self.desc_combo.text = ""
        self.start_edit.text = ""
        self.end_edit.text = ""
        self.hours_spin.setValue(0.0)
        self._set_time_mode(TimeMode.DURATION)
        self.notes_hint.setVisible(False)
        self._toggle_edit_mode(False)
        self.day_tree.clearSelection()

    # --- Timer ---

    def _toggle_timer(self):
        if self._timer_start is None:
            self._timer_start = datetime.now()
            self.start_edit.text = self._timer_start.strftime("%H:%M")
            self._set_time_mode(TimeMode.RANGE)

            self.timer_btn.setText("Timer beenden")
            self.timer_btn.setObjectName("success")
            self.timer_btn.setStyle(self.timer_btn.style())  # force stylesheet refresh
            self.timer_abort_btn.setVisible(True)
            self._timer.start(1000)
            self._update_timer_display()
        else:
            end_time = datetime.now()
            self.end_edit.text = end_time.strftime("%H:%M")
            self._save_entry()
            self._abort_timer()

    def _abort_timer(self):
        self._timer_start = None
        self._timer.stop()
        self.timer_btn.setText("Timer starten")
        self.timer_btn.setObjectName("secondary")
        self.timer_btn.setStyle(self.timer_btn.style())
        self.timer_abort_btn.setVisible(False)
        self.timer_label.setText("")

    def _update_timer_display(self):
        if self._timer_start is None:
            return
        diff = datetime.now() - self._timer_start
        total_secs = int(diff.total_seconds())
        h = total_secs // 3600
        m = (total_secs % 3600) // 60
        s = total_secs % 60
        self.timer_label.setText(f"{h:02d}:{m:02d}:{s:02d}")

    # --- SAP ITP Copy ---

    def _copy_for_sap(self):
        current = self.day_tree.currentItem()
        if not current:
            QMessageBox.information(self, "Kopieren", "Bitte einen Eintrag auswählen.")
            return

        entry_id = current.data(0, Qt.UserRole)
        if entry_id is None:
            return  # Summary row, not an entry

        entries = self.db.get_entries_for_date(self.date_nav.selected_date)
        entry = next((e for e in entries if e.id == entry_id), None)
        if not entry:
            return
        text = self._entry_to_sap_line(entry)

        QApplication.clipboard().setText(text)
        self._show_status("In Zwischenablage kopiert.")

    def _copy_day_for_sap(self):
        entries = self.db.get_entries_for_date(self.date_nav.selected_date)
        if not entries:
            QMessageBox.information(self, "Kopieren", "Keine Einträge für diesen Tag.")
            return

        lines = [self._entry_to_sap_line(e) for e in entries]
        QApplication.clipboard().setText("\n".join(lines))
        self._show_status(f"{len(entries)} Einträge in Zwischenablage kopiert.")

    def _open_sap_export(self):
        dialog = SapExportDialog(self.db, self.date_nav.selected_date, self)
        if dialog.exec():
            self._show_status("SAP ITP Daten in Zwischenablage kopiert.")

    def _entry_to_sap_line(self, entry: TimeEntry) -> str:
        day = entry.date
        weekday_index = day.weekday()
        hours_text = f"{entry.hours:.2f}".replace(".", ",")

        day_hours = [""] * 5  # Mo-Fr
        if 0 <= weekday_index < 5:
            day_hours[weekday_index] = hours_text

        # SAP GUI ITP: Leistungsart | PSP | Bezeichnung | Bezeichnung | StatKz | ME | Summe | Mo-Fr
        columns = [
            entry.activity_type,
            entry.psp,
            entry.description,
            "",  # Bezeichnung 2
            "",  # StatKz
            "",  # ME
            "",  # Summe (auto-calculated by SAP)
            *day_hours,
        ]
        return "\t".join(columns)

    # --- Helpers ---

    def _show_status(self, msg: str, duration: int = 3000):
        self.status_bar.showMessage(msg, duration)

    def _open_preset_manager(self):
        dialog = PresetManagerDialog(self.db, self)
        dialog.presets_changed.connect(self._refresh_presets)
        dialog.exec()

    def _open_statistics(self):
        dialog = StatisticsDialog(self.db, self.date_nav.selected_date, self)
        dialog.exec()
