"""Statistics dialog for TimeTrac — hours by PSP with billable/non-billable breakdown."""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .database import Database


# ── Horizontal bar chart widget (pure QPainter, no external deps) ──

class BarChartWidget(QWidget):
    """Custom widget that draws horizontal bars for PSP hours."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[dict] = []
        self._max_hours = 1.0
        self.setMinimumHeight(60)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, data: list[dict]):
        self._data = data
        self._max_hours = max((d["hours"] for d in data), default=1.0) or 1.0
        # Height: 44px per bar + 30px padding
        self.setMinimumHeight(max(60, len(data) * 44 + 30))
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        label_width = 140
        bar_area_x = label_width + 10
        bar_area_w = w - bar_area_x - 80  # leave room for value text
        bar_height = 26
        row_height = 44
        y_offset = 10

        billable_color = QColor(theme.ACCENT)
        non_billable_color = QColor("#f59e0b")  # amber

        label_font = QFont("Segoe UI", 11)
        value_font = QFont("Segoe UI", 10, QFont.Bold)
        painter.setFont(label_font)

        for i, item in enumerate(self._data):
            y = y_offset + i * row_height
            psp = item["psp"] or "(kein PSP)"
            hours = item["hours"]
            billable = item.get("billable", True)

            # Label
            painter.setPen(QPen(QColor(theme.TEXT_PRIMARY)))
            painter.setFont(label_font)
            label_rect = QRect(4, y, label_width, bar_height)
            elided = painter.fontMetrics().elidedText(psp, Qt.ElideRight, label_width - 8)
            painter.drawText(label_rect, Qt.AlignVCenter | Qt.AlignRight, elided)

            # Bar
            bar_w = max(4, int((hours / self._max_hours) * bar_area_w))
            color = billable_color if billable else non_billable_color
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(bar_area_x, y + 2, bar_w, bar_height - 4, 4, 4)

            # Value
            painter.setPen(QPen(QColor(theme.TEXT_PRIMARY)))
            painter.setFont(value_font)
            painter.drawText(bar_area_x + bar_w + 8, y, 70, bar_height,
                             Qt.AlignVCenter | Qt.AlignLeft, f"{hours:.2f} h")

        # Legend
        legend_y = y_offset + len(self._data) * row_height + 4
        painter.setFont(QFont("Segoe UI", 10))

        painter.setBrush(QBrush(billable_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bar_area_x, legend_y, 14, 14, 3, 3)
        painter.setPen(QPen(QColor(theme.TEXT_SECONDARY)))
        painter.drawText(bar_area_x + 20, legend_y, 100, 14, Qt.AlignVCenter, "Fakturierbar")

        painter.setBrush(QBrush(non_billable_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bar_area_x + 130, legend_y, 14, 14, 3, 3)
        painter.setPen(QPen(QColor(theme.TEXT_SECONDARY)))
        painter.drawText(bar_area_x + 156, legend_y, 130, 14, Qt.AlignVCenter, "Nicht fakturierbar")

        painter.end()


# ── Donut / ring widget for billable vs non-billable ──

class DonutWidget(QWidget):
    """Small donut chart showing billable vs non-billable ratio."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._billable = 0.0
        self._non_billable = 0.0
        self.setFixedSize(160, 160)

    def set_data(self, billable: float, non_billable: float):
        self._billable = billable
        self._non_billable = non_billable
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        total = self._billable + self._non_billable
        if total <= 0:
            painter.setPen(QPen(QColor(theme.TEXT_MUTED)))
            painter.drawText(self.rect(), Qt.AlignCenter, "Keine Daten")
            painter.end()
            return

        size = min(self.width(), self.height()) - 10
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2
        rect = QRect(x, y, size, size)

        arc_width = 22
        billable_color = QColor(theme.ACCENT)
        non_billable_color = QColor("#f59e0b")

        pen = QPen()
        pen.setWidth(arc_width)
        pen.setCapStyle(Qt.RoundCap)

        # Background ring
        pen.setColor(QColor(theme.BG_TERTIARY))
        painter.setPen(pen)
        painter.drawArc(rect.adjusted(arc_width // 2, arc_width // 2,
                                       -arc_width // 2, -arc_width // 2),
                        0, 360 * 16)

        # Billable arc
        billable_span = int((self._billable / total) * 360 * 16)
        pen.setColor(billable_color)
        painter.setPen(pen)
        painter.drawArc(rect.adjusted(arc_width // 2, arc_width // 2,
                                       -arc_width // 2, -arc_width // 2),
                        90 * 16, -billable_span)

        # Non-billable arc
        if self._non_billable > 0:
            pen.setColor(non_billable_color)
            painter.setPen(pen)
            painter.drawArc(rect.adjusted(arc_width // 2, arc_width // 2,
                                           -arc_width // 2, -arc_width // 2),
                            90 * 16 - billable_span, -int((self._non_billable / total) * 360 * 16))

        # Center text
        painter.setPen(QPen(QColor(theme.TEXT_PRIMARY)))
        painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
        pct = int((self._billable / total) * 100) if total > 0 else 0
        painter.drawText(rect, Qt.AlignCenter, f"{pct}%")

        painter.end()


# ── Main statistics dialog ──

class StatisticsDialog(QDialog):
    """Dialog showing time statistics by PSP with billable breakdown."""

    def __init__(self, db: Database, current_date: date, parent=None):
        super().__init__(parent)
        self.db = db
        self._current_date = current_date
        self.setWindowTitle("Statistik")
        self.setMinimumSize(900, 620)
        self.resize(1000, 700)
        self._build_ui()
        self._on_period_changed()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Zeitstatistik")
        title.setObjectName("title")
        layout.addWidget(title)

        # Period selector row
        period_frame = QFrame()
        period_frame.setObjectName("card")
        period_layout = QHBoxLayout(period_frame)
        period_layout.setContentsMargins(14, 10, 14, 10)
        period_layout.setSpacing(12)

        period_layout.addWidget(QLabel("Zeitraum:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Diese Woche", "Dieser Monat", "Benutzerdefiniert"])
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        period_layout.addWidget(self.period_combo)

        period_layout.addWidget(QLabel("Von:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd.MM.yyyy")
        self.start_date.dateChanged.connect(self._on_custom_date_changed)
        period_layout.addWidget(self.start_date)

        period_layout.addWidget(QLabel("Bis:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd.MM.yyyy")
        self.end_date.dateChanged.connect(self._on_custom_date_changed)
        period_layout.addWidget(self.end_date)

        period_layout.addStretch()
        layout.addWidget(period_frame)

        # Stats content: chart + donut side by side
        content = QHBoxLayout()
        content.setSpacing(16)

        # Left: bar chart + table
        left = QVBoxLayout()
        left.setSpacing(10)

        chart_label = QLabel("Stunden pro PSP")
        chart_label.setObjectName("sectionLabel")
        left.addWidget(chart_label)

        self.bar_chart = BarChartWidget()
        chart_frame = QFrame()
        chart_frame.setObjectName("card")
        chart_inner = QVBoxLayout(chart_frame)
        chart_inner.setContentsMargins(8, 8, 8, 8)
        chart_inner.addWidget(self.bar_chart)
        left.addWidget(chart_frame, 1)

        # Detail table
        self.detail_tree = QTreeWidget()
        self.detail_tree.setHeaderLabels(["PSP", "Leistungsart", "Stunden", "Fakturierbar"])
        self.detail_tree.setRootIsDecorated(False)
        self.detail_tree.setAlternatingRowColors(True)
        self.detail_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.detail_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.detail_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.detail_tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.detail_tree.setMaximumHeight(200)
        left.addWidget(self.detail_tree)

        content.addLayout(left, 3)

        # Right: donut + summary cards
        right = QVBoxLayout()
        right.setSpacing(12)

        donut_label = QLabel("Fakturierbar / Nicht fakt.")
        donut_label.setObjectName("sectionLabel")
        right.addWidget(donut_label, 0, Qt.AlignHCenter)

        self.donut = DonutWidget()
        right.addWidget(self.donut, 0, Qt.AlignHCenter)

        # Summary cards
        self.total_label = self._make_summary_card("Gesamt", "0,00 h")
        self.billable_label = self._make_summary_card("Fakturierbar", "0,00 h")
        self.non_billable_label = self._make_summary_card("Nicht fakt.", "0,00 h")
        self.avg_label = self._make_summary_card("Ø pro Tag", "0,00 h")

        right.addWidget(self.total_label)
        right.addWidget(self.billable_label)
        right.addWidget(self.non_billable_label)
        right.addWidget(self.avg_label)
        right.addStretch()

        content.addLayout(right, 1)
        layout.addLayout(content, 1)

        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Schließen")
        close_btn.setObjectName("secondary")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

    def _make_summary_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: 11px;")
        card_layout.addWidget(lbl_title)

        lbl_value = QLabel(value)
        lbl_value.setObjectName("summaryValue")
        lbl_value.setStyleSheet("font-size: 18px; font-weight: bold;")
        card_layout.addWidget(lbl_value)

        return card

    def _get_date_range(self) -> tuple[date, date]:
        idx = self.period_combo.currentIndex()
        if idx == 0:  # This week
            start = self._current_date - timedelta(days=self._current_date.weekday())
            end = start + timedelta(days=6)
        elif idx == 1:  # This month
            start = self._current_date.replace(day=1)
            # Last day of month
            if self._current_date.month == 12:
                end = self._current_date.replace(year=self._current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = self._current_date.replace(month=self._current_date.month + 1, day=1) - timedelta(days=1)
        else:  # Custom
            start = self.start_date.date().toPython()
            end = self.end_date.date().toPython()
        return start, end

    def _on_period_changed(self):
        idx = self.period_combo.currentIndex()
        is_custom = idx == 2

        # Set default dates for non-custom modes
        if idx == 0:
            start = self._current_date - timedelta(days=self._current_date.weekday())
            end = start + timedelta(days=6)
        elif idx == 1:
            start = self._current_date.replace(day=1)
            if self._current_date.month == 12:
                end = self._current_date.replace(year=self._current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = self._current_date.replace(month=self._current_date.month + 1, day=1) - timedelta(days=1)
        else:
            start = self._current_date - timedelta(days=self._current_date.weekday())
            end = start + timedelta(days=6)

        self.start_date.blockSignals(True)
        self.end_date.blockSignals(True)
        self.start_date.setDate(start)
        self.end_date.setDate(end)
        self.start_date.setEnabled(is_custom)
        self.end_date.setEnabled(is_custom)
        self.start_date.blockSignals(False)
        self.end_date.blockSignals(False)

        self._refresh_stats()

    def _on_custom_date_changed(self):
        if self.period_combo.currentIndex() == 2:
            self._refresh_stats()

    def _refresh_stats(self):
        start, end = self._get_date_range()

        # Get merged data for chart
        merged = self.db.get_hours_by_psp_merged(start, end)
        self.bar_chart.set_data(merged)

        # Get detailed data for table
        detailed = self.db.get_hours_by_psp(start, end)
        self.detail_tree.clear()
        for item_data in detailed:
            billable_text = "Ja" if item_data["billable"] else "Nein"
            item = QTreeWidgetItem([
                item_data["psp"] or "(kein PSP)",
                item_data["activity_type"],
                f"{item_data['hours']:.2f}",
                billable_text,
            ])
            self.detail_tree.addTopLevelItem(item)

        # Calculate summaries
        total_hours = sum(d["hours"] for d in merged)
        billable_hours = sum(d["hours"] for d in merged if d["billable"])
        non_billable_hours = sum(d["hours"] for d in merged if not d["billable"])

        # Count working days in range
        days = (end - start).days + 1
        working_days = sum(1 for i in range(days) if (start + timedelta(days=i)).weekday() < 5)
        avg = total_hours / working_days if working_days > 0 else 0

        # Update summary cards
        self._set_summary_value(self.total_label, f"{total_hours:.2f} h")
        self._set_summary_value(self.billable_label, f"{billable_hours:.2f} h")
        self._set_summary_value(self.non_billable_label, f"{non_billable_hours:.2f} h")
        self._set_summary_value(self.avg_label, f"{avg:.2f} h")

        # Update donut
        self.donut.set_data(billable_hours, non_billable_hours)

    def _set_summary_value(self, card: QFrame, text: str):
        value_label = card.findChild(QLabel, "summaryValue")
        if value_label:
            value_label.setText(text)
