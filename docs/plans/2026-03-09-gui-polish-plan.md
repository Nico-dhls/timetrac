# GUI Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Comprehensive visual refresh of TimeTrac - fix spacing, improve hierarchy, modernize feel, default to Duration mode.

**Architecture:** Pure styling and layout changes across 3 files. No data model or database changes. The theme stylesheet gets updated first, then layout code in main_window and widgets.

**Tech Stack:** PySide6 (Qt for Python), QSS stylesheets, Python 3.12

**Test command:** `.venv/bin/python -m pytest tests/ -v`

---

### Task 1: Update Theme - Typography, Button Depth, Input Padding, Divider

**Files:**
- Modify: `timetrac/theme.py`

**Step 1: Update typography and button depth in theme.py**

In `timetrac/theme.py`, make these changes to the `STYLESHEET` string:

1. Title font size 22px → 24px:
```python
# Change QLabel#title
    QLabel#title {{
        font-size: 24px;
        font-weight: bold;
    }}
```

2. Section label with letter-spacing:
```python
# Change QLabel#sectionLabel
    QLabel#sectionLabel {{
        font-size: 11px;
        color: {TEXT_SECONDARY};
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
```

3. Input fields padding 8px → 10px:
```python
# Change QLineEdit, QSpinBox, QDoubleSpinBox
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {BG_TERTIARY};
        border: 1px solid {BORDER};
        border-bottom: 2px solid #2a2a3c;
        border-radius: 6px;
        padding: 10px 12px;
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT};
    }}
```

4. ComboBox padding:
```python
# Change QComboBox
    QComboBox {{
        background-color: {BG_TERTIARY};
        border: 1px solid {BORDER};
        border-bottom: 2px solid #2a2a3c;
        border-radius: 6px;
        padding: 10px 12px;
        color: {TEXT_PRIMARY};
        min-width: 80px;
    }}
```

5. All button border-bottom 3px → 2px (QPushButton, #secondary, #danger, #success, #navButton). Update hover/pressed padding accordingly:

For default QPushButton:
```css
    QPushButton {{
        ...
        border-bottom: 2px solid #5b21b6;
    }}

    QPushButton:hover {{
        ...
        border-bottom: 2px solid #4c1d95;
        padding-top: 7px;
        padding-bottom: 9px;
    }}

    QPushButton:pressed {{
        ...
        border-bottom: 1px solid #4c1d95;
        padding-top: 9px;
        padding-bottom: 8px;
    }}

    QPushButton:disabled {{
        ...
        border-bottom: 2px solid {BORDER};
    }}
```

Apply same 3px→2px pattern for `#secondary`, `#danger`, `#success`, `#navButton`.

6. Tab bar padding:
```python
    QTabBar::tab {{
        background-color: {BG_TERTIARY};
        color: {TEXT_SECONDARY};
        padding: 10px 20px;
        border: none;
        border-bottom: 2px solid transparent;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}
```

7. Add divider style and segmented control styles at end of STYLESHEET, before the closing `"""`:
```python
    /* Divider */
    QFrame#divider {{
        background-color: {BORDER};
        border: none;
        max-height: 1px;
        min-height: 1px;
    }}

    /* Segmented control */
    QPushButton#segmentLeft {{
        background-color: transparent;
        border: 1px solid {BORDER};
        border-right: none;
        border-radius: 0px;
        border-top-left-radius: 6px;
        border-bottom-left-radius: 6px;
        color: {TEXT_SECONDARY};
        font-weight: normal;
        padding: 6px 14px;
        font-size: 12px;
        border-bottom: 2px solid {BORDER};
    }}

    QPushButton#segmentRight {{
        background-color: transparent;
        border: 1px solid {BORDER};
        border-radius: 0px;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
        color: {TEXT_SECONDARY};
        font-weight: normal;
        padding: 6px 14px;
        font-size: 12px;
        border-bottom: 2px solid {BORDER};
    }}

    QPushButton#segmentLeft:checked, QPushButton#segmentRight:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
        border-bottom: 2px solid #5b21b6;
        color: white;
        font-weight: bold;
    }}

    QPushButton#segmentLeft:hover, QPushButton#segmentRight:hover {{
        background-color: {BG_HOVER};
        color: {TEXT_PRIMARY};
    }}

    QPushButton#segmentLeft:checked:hover, QPushButton#segmentRight:checked:hover {{
        background-color: {ACCENT_HOVER};
        color: white;
    }}
```

**Step 2: Run tests**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All 18 tests pass (theme changes are pure CSS, no logic).

**Step 3: Commit**

```bash
git add timetrac/theme.py
git commit -m "Refine theme: typography, button depth, input padding, dividers, segments"
```

---

### Task 2: Add Divider Helper to Widgets

**Files:**
- Modify: `timetrac/widgets.py`

**Step 1: Add make_divider helper**

Add after the `make_label` function (after line 49 in `timetrac/widgets.py`):

```python
def make_divider(parent=None) -> QFrame:
    """Create a horizontal divider line."""
    frame = QFrame(parent)
    frame.setObjectName("divider")
    frame.setFrameShape(QFrame.HLine)
    return frame
```

**Step 2: Run tests**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All 18 pass.

**Step 3: Commit**

```bash
git add timetrac/widgets.py
git commit -m "Add make_divider helper widget"
```

---

### Task 3: Refactor Left Panel - Remove Cards, Add Dividers, Segmented Time Toggle

**Files:**
- Modify: `timetrac/main_window.py:40` (import make_divider)
- Modify: `timetrac/main_window.py:103-290` (_build_left_panel method)

**Step 1: Update import**

In `timetrac/main_window.py` line 40, add `make_divider` to the import:
```python
from .widgets import DateNavigator, EditableComboBox, TimeEdit, make_card, make_divider, make_label
```

**Step 2: Rewrite _build_left_panel**

Replace the entire `_build_left_panel` method (lines 103-290) with:

```python
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
        layout.addWidget(make_label("PSP & Leistungsart", "sectionLabel"))

        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(12)

        self.psp_combo = EditableComboBox()
        self.psp_combo.setPlaceholderText("PSP-Element")
        fields_layout.addWidget(self.psp_combo, 1)

        self.type_combo = EditableComboBox()
        self.type_combo.setPlaceholderText("Leistungsart")
        fields_layout.addWidget(self.type_combo, 1)

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
```

**Step 3: Replace _toggle_time_mode with _set_time_mode**

Replace the `_toggle_time_mode` method (lines 606-616) with:

```python
    def _set_time_mode(self, mode: TimeMode):
        self._time_mode = mode
        is_range = mode == TimeMode.RANGE
        self.range_widget.setVisible(is_range)
        self.duration_widget.setVisible(not is_range)
        self.range_seg_btn.setChecked(is_range)
        self.duration_seg_btn.setChecked(not is_range)
```

**Step 4: Update _on_entry_selected to use _set_time_mode**

In the `_on_entry_selected` method, replace the mode-switching block (lines 565-577) with:

```python
        if entry.mode == TimeMode.RANGE:
            self._set_time_mode(TimeMode.RANGE)
            self.start_edit.text = entry.start_time
            self.end_edit.text = entry.end_time
        else:
            self._set_time_mode(TimeMode.DURATION)
            self.hours_spin.setValue(entry.hours)
```

**Step 5: Update _reset_form to default to Duration**

In `_reset_form`, replace lines 710-713:
```python
        # Old:
        self._time_mode = TimeMode.RANGE
        self.range_widget.setVisible(True)
        self.duration_widget.setVisible(False)
        self.mode_btn.setText("Modus: Stunden")

        # New:
        self._set_time_mode(TimeMode.DURATION)
```

**Step 6: Update _toggle_timer to use _set_time_mode**

In `_toggle_timer`, replace lines 724-727:
```python
        # Old:
        self._time_mode = TimeMode.RANGE
        self.range_widget.setVisible(True)
        self.duration_widget.setVisible(False)
        self.mode_btn.setText("Modus: Stunden")

        # New:
        self._set_time_mode(TimeMode.RANGE)
```

**Step 7: Remove old mode_btn references**

Remove line 180: `self.mode_btn.clicked.connect(self._toggle_time_mode)` — this button no longer exists.

**Step 8: Run tests**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All 18 pass.

**Step 9: Commit**

```bash
git add timetrac/main_window.py
git commit -m "Refactor left panel: dividers, segmented time toggle, default duration mode"
```

---

### Task 4: Refactor Right Panel - Flat Day View, Integrated Header

**Files:**
- Modify: `timetrac/main_window.py:292-407` (_build_right_panel method)
- Modify: `timetrac/main_window.py:417-453` (_refresh_day_view method)

**Step 1: Rewrite _build_right_panel**

Replace the entire `_build_right_panel` method with:

```python
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

        # Copy buttons toolbar
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
```

**Step 2: Rewrite _refresh_day_view for flat rows with smart grouping**

Replace the entire `_refresh_day_view` method with:

```python
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
                    time_info = f"{entry.start_time}–{entry.end_time}"
                item = QTreeWidgetItem([
                    entry.psp,
                    entry.activity_type,
                    entry.description,
                    time_info if time_info else "–",
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
```

**Step 3: Run tests**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All 18 pass.

**Step 4: Commit**

```bash
git add timetrac/main_window.py
git commit -m "Refactor right panel: flat day view, smart grouping, integrated header"
```

---

### Task 5: Visual Smoke Test & Screenshot Update

**Step 1: Launch the app and verify visually**

Run: `.venv/bin/python -m timetrac`

Verify:
- Left panel: Dividers between sections, no card wrappers on PSP/Time/Description
- Segmented "Dauer | Zeitspanne" toggle shows, Duration mode active by default
- Buttons all equal height
- Right panel: No "Übersicht" title, Statistik is a flat button above tabs
- Day view: Flat rows, no redundant parent/child, summary only for multi-entry groups
- Typography: Title is larger, section labels have letter-spacing
- Buttons: Subtler press depth (2px instead of 3px)

**Step 2: Test interactions**

- Click "Zeitspanne" segment → Range inputs appear, "Dauer" deselects
- Click "Dauer" segment → Duration spinner appears, "Zeitspanne" deselects
- Start timer → switches to Range mode, segments update
- Add an entry with Duration mode → saves correctly
- Select existing entry → form populates, correct mode shown
- Reset form → returns to Duration mode

**Step 3: Run tests one final time**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All 18 pass.

**Step 4: Commit all remaining changes**

```bash
git add -A
git commit -m "Polish GUI: modern refinement with duration default"
```
