"""Dark theme palette and styling for TimeTrac."""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QPushButton

# Color palette
BG_PRIMARY = "#1e1e2e"       # Main background
BG_SECONDARY = "#2a2a3c"     # Cards / panels
BG_TERTIARY = "#33334d"      # Input fields
BG_HOVER = "#3d3d5c"         # Hover state
ACCENT = "#7c3aed"           # Primary accent (purple)
ACCENT_HOVER = "#6d28d9"     # Accent hover
ACCENT_LIGHT = "#a78bfa"     # Light accent for text
DANGER = "#ef4444"           # Delete / danger
DANGER_HOVER = "#dc2626"
SUCCESS = "#22c55e"          # Success / timer running
TEXT_PRIMARY = "#f1f5f9"     # Main text
TEXT_SECONDARY = "#94a3b8"   # Muted text
TEXT_MUTED = "#64748b"       # Very muted
BORDER = "#3d3d5c"           # Borders
SELECTED_ROW = "#4c1d95"     # Selected row in table
GROUP_ROW = "#2d2250"        # Group header row


STYLESHEET = f"""
    * {{
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 13px;
    }}

    QMainWindow, QDialog {{
        background-color: {BG_PRIMARY};
    }}

    QWidget {{
        color: {TEXT_PRIMARY};
    }}

    /* Cards / Frames */
    QFrame#card {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
    }}

    QFrame#cardFlat {{
        background-color: transparent;
        border: none;
    }}

    /* Labels */
    QLabel {{
        color: {TEXT_PRIMARY};
        background: transparent;
        border: none;
    }}

    QLabel#title {{
        font-size: 24px;
        font-weight: bold;
    }}

    QLabel#subtitle {{
        font-size: 13px;
        color: {TEXT_SECONDARY};
    }}

    QLabel#sectionLabel {{
        font-size: 11px;
        color: {TEXT_SECONDARY};
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    QLabel#timerDisplay {{
        font-size: 28px;
        font-weight: bold;
        color: {ACCENT_LIGHT};
    }}

    QLabel#notesHint {{
        font-size: 12px;
        color: {ACCENT_LIGHT};
        font-style: italic;
        padding: 4px 8px;
        background-color: {GROUP_ROW};
        border-radius: 4px;
    }}

    /* Input fields */
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {BG_TERTIARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 10px 12px;
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT};
    }}

    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {ACCENT};
    }}

    QTextEdit {{
        background-color: {BG_TERTIARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px;
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT};
    }}

    QTextEdit:focus {{
        border: 1px solid {ACCENT};
    }}

    /* ComboBox */
    QComboBox {{
        background-color: {BG_TERTIARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 10px 12px;
        color: {TEXT_PRIMARY};
        min-width: 80px;
    }}

    QComboBox:focus {{
        border: 1px solid {ACCENT};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 0px;
    }}

    QComboBox {{
        padding-right: 8px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {BG_TERTIARY};
        border: 1px solid {BORDER};
        selection-background-color: {ACCENT};
        color: {TEXT_PRIMARY};
        outline: none;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {ACCENT};
        color: white;
        border: 1px solid {ACCENT};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background-color: {ACCENT_HOVER};
        border-color: {ACCENT_HOVER};
    }}

    QPushButton:pressed {{
        background-color: #5b21b6;
        border-color: #4c1d95;
    }}

    QPushButton:disabled {{
        background-color: {BG_TERTIARY};
        color: {TEXT_MUTED};
        border-color: {BORDER};
    }}

    QPushButton#secondary {{
        background-color: transparent;
        border: 1px solid {BORDER};
        color: {TEXT_PRIMARY};
        font-weight: normal;
    }}

    QPushButton#secondary:hover {{
        background-color: {BG_HOVER};
        border-color: {ACCENT_LIGHT};
        color: {ACCENT_LIGHT};
    }}

    QPushButton#secondary:pressed {{
        background-color: {BG_TERTIARY};
        border-color: {BORDER};
    }}

    QPushButton#danger {{
        background-color: {DANGER};
        border-color: {DANGER};
    }}

    QPushButton#danger:hover {{
        background-color: {DANGER_HOVER};
        border-color: {DANGER_HOVER};
    }}

    QPushButton#danger:pressed {{
        background-color: #b91c1c;
        border-color: #991b1b;
    }}

    QPushButton#success {{
        background-color: {SUCCESS};
        color: white;
        border-color: {SUCCESS};
    }}

    QPushButton#success:hover {{
        background-color: #16a34a;
        border-color: #16a34a;
    }}

    QPushButton#success:pressed {{
        background-color: #15803d;
        border-color: #166534;
    }}

    QPushButton#flat {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: none;
        font-weight: normal;
        padding: 4px 8px;
    }}

    QPushButton#flat:hover {{
        color: {ACCENT_LIGHT};
        background-color: {BG_HOVER};
    }}

    QPushButton#flat:pressed {{
        color: {ACCENT};
        background-color: {BG_TERTIARY};
    }}

    QPushButton#navButton {{
        background-color: transparent;
        border: 1px solid {BORDER};
        color: {TEXT_PRIMARY};
        font-weight: normal;
        padding: 6px 12px;
        min-width: 32px;
    }}

    QPushButton#navButton:hover {{
        background-color: {BG_HOVER};
        border-color: {ACCENT_LIGHT};
        color: {ACCENT_LIGHT};
    }}

    QPushButton#navButton:pressed {{
        background-color: {BG_TERTIARY};
        border-color: {BORDER};
    }}

    /* Checkbox styling */
    QCheckBox {{
        spacing: 8px;
        color: {TEXT_PRIMARY};
    }}

    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 2px solid {BORDER};
        background-color: {BG_TERTIARY};
    }}

    QCheckBox::indicator:hover {{
        border-color: {ACCENT_LIGHT};
    }}

    QCheckBox::indicator:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
    }}

    /* Date edit */
    QDateEdit {{
        background-color: {BG_TERTIARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        color: {TEXT_PRIMARY};
    }}

    QDateEdit:focus {{
        border: 1px solid {ACCENT};
    }}

    QDateEdit::drop-down {{
        border: none;
        width: 24px;
    }}

    /* Table / Tree */
    QTreeWidget, QTableWidget {{
        background-color: {BG_SECONDARY};
        alternate-background-color: {BG_TERTIARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        outline: none;
        gridline-color: {BORDER};
    }}

    QTreeWidget::item, QTableWidget::item {{
        padding: 6px 8px;
        border: none;
    }}

    QTreeWidget::item:selected, QTableWidget::item:selected {{
        background-color: {SELECTED_ROW};
    }}

    QTreeWidget::item:hover, QTableWidget::item:hover {{
        background-color: {BG_HOVER};
    }}

    QHeaderView::section {{
        background-color: {BG_TERTIARY};
        color: {TEXT_SECONDARY};
        border: none;
        border-bottom: 1px solid {BORDER};
        padding: 8px 10px;
        font-weight: bold;
        font-size: 12px;
    }}

    /* ScrollBar */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {BORDER};
        border-radius: 4px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {TEXT_MUTED};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background-color: transparent;
        height: 8px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {BORDER};
        border-radius: 4px;
        min-width: 30px;
    }}

    /* Splitter */
    QSplitter::handle {{
        background-color: {BORDER};
        width: 1px;
    }}

    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        border-radius: 6px;
        background-color: {BG_SECONDARY};
    }}

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

    QTabBar::tab:selected {{
        color: {ACCENT_LIGHT};
        border-bottom: 2px solid {ACCENT};
        background-color: {BG_SECONDARY};
    }}

    QTabBar::tab:hover {{
        color: {TEXT_PRIMARY};
        background-color: {BG_HOVER};
    }}

    /* Status bar */
    QStatusBar {{
        background-color: {BG_SECONDARY};
        color: {TEXT_SECONDARY};
        border-top: 1px solid {BORDER};
    }}

    /* Tooltips */
    QToolTip {{
        background-color: {BG_TERTIARY};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        padding: 6px 10px;
        border-radius: 4px;
    }}

    /* Calendar popup */
    QCalendarWidget {{
        background-color: {BG_SECONDARY};
    }}

    QCalendarWidget QWidget {{
        alternate-background-color: {BG_TERTIARY};
    }}

    QCalendarWidget QAbstractItemView {{
        background-color: {BG_SECONDARY};
        selection-background-color: {ACCENT};
        selection-color: white;
    }}

    QCalendarWidget QToolButton {{
        color: {TEXT_PRIMARY};
        background-color: transparent;
        border: none;
        padding: 4px 8px;
    }}

    QCalendarWidget QToolButton:hover {{
        background-color: {BG_HOVER};
        border-radius: 4px;
    }}

    QCalendarWidget #qt_calendar_navigationbar {{
        background-color: {BG_TERTIARY};
        border-bottom: 1px solid {BORDER};
        padding: 4px;
    }}

    /* Divider */
    QFrame#divider {{
        background-color: {BORDER};
        border: none;
        max-height: 1px;
        min-height: 1px;
    }}

    /* Segmented controls */
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
    }}

    QPushButton#segmentLeft:checked, QPushButton#segmentRight:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
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
"""


def apply_theme(app: QApplication):
    app.setStyleSheet(STYLESHEET)

    # Set pointing hand cursor on all buttons globally
    from PySide6.QtCore import Qt

    original_init = QPushButton.__init__

    def _patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.setCursor(Qt.PointingHandCursor)

    QPushButton.__init__ = _patched_init
