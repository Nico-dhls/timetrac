"""Preset manager dialog for TimeTrac."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from .database import Database
from .models import Preset


class PresetManagerDialog(QDialog):
    """Dialog for managing presets with notes."""

    presets_changed = Signal()

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Vorlagen verwalten")
        self.setMinimumSize(750, 500)
        self.resize(850, 550)
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QLabel("Vorlagen setzen PSP und Leistungsart automatisch.\n"
                        "Notizen können Hinweise zur Syntax der Kurzbeschreibung enthalten.")
        header.setObjectName("subtitle")
        layout.addWidget(header)

        # Main content: list + form
        splitter = QSplitter(Qt.Horizontal)

        # Left: preset list
        left = QFrame()
        left.setObjectName("card")
        left_layout = QVBoxLayout(left)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "PSP", "Leistungsart"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.currentItemChanged.connect(self._on_select)
        left_layout.addWidget(self.tree)

        splitter.addWidget(left)

        # Right: edit form
        right = QFrame()
        right.setObjectName("card")
        right_layout = QVBoxLayout(right)

        form_title = QLabel("Vorlage bearbeiten")
        form_title.setObjectName("title")
        form_title.setStyleSheet("font-size: 16px;")
        right_layout.addWidget(form_title)

        grid = QGridLayout()
        grid.setSpacing(8)

        grid.addWidget(QLabel("Name:"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("z.B. Projekt Alpha")
        grid.addWidget(self.name_edit, 0, 1)

        grid.addWidget(QLabel("PSP:"), 1, 0)
        self.psp_edit = QLineEdit()
        self.psp_edit.setPlaceholderText("z.B. PSP-12345")
        grid.addWidget(self.psp_edit, 1, 1)

        grid.addWidget(QLabel("Leistungsart:"), 2, 0)
        self.type_edit = QLineEdit()
        self.type_edit.setPlaceholderText("z.B. Entwicklung")
        grid.addWidget(self.type_edit, 2, 1)

        grid.addWidget(QLabel("Notizen:"), 3, 0, Qt.AlignTop)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(
            "Hinweise zur Beschreibungs-Syntax, z.B.:\n"
            "Kunde X: [Ticketnr] - Kurzbeschreibung\n"
            "Kunde Y: PROJ-XXX: Beschreibung"
        )
        self.notes_edit.setMaximumHeight(120)
        grid.addWidget(self.notes_edit, 3, 1)

        right_layout.addLayout(grid)

        # Form buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.add_btn = QPushButton("Hinzufügen")
        self.add_btn.clicked.connect(self._add_preset)

        self.update_btn = QPushButton("Aktualisieren")
        self.update_btn.clicked.connect(self._update_preset)
        self.update_btn.setVisible(False)

        self.delete_btn = QPushButton("Löschen")
        self.delete_btn.setObjectName("danger")
        self.delete_btn.clicked.connect(self._delete_preset)
        self.delete_btn.setVisible(False)

        self.clear_btn = QPushButton("Felder leeren")
        self.clear_btn.setObjectName("secondary")
        self.clear_btn.clicked.connect(self._clear_form)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_btn)
        right_layout.addLayout(btn_layout)
        right_layout.addStretch()

        splitter.addWidget(right)
        splitter.setSizes([400, 400])

        layout.addWidget(splitter, 1)

        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Schließen")
        close_btn.setObjectName("secondary")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

    def _refresh_list(self):
        self.tree.clear()
        self._presets = self.db.get_presets()
        for preset in self._presets:
            item = QTreeWidgetItem([preset.name, preset.psp, preset.activity_type])
            item.setData(0, Qt.UserRole, preset.id)
            self.tree.addTopLevelItem(item)

    def _on_select(self, current, previous):
        if current is None:
            self.update_btn.setVisible(False)
            self.delete_btn.setVisible(False)
            return

        preset_id = current.data(0, Qt.UserRole)
        preset = next((p for p in self._presets if p.id == preset_id), None)
        if preset is None:
            return

        self.name_edit.setText(preset.name)
        self.psp_edit.setText(preset.psp)
        self.type_edit.setText(preset.activity_type)
        self.notes_edit.setPlainText(preset.notes)

        self.update_btn.setVisible(True)
        self.delete_btn.setVisible(True)

    def _get_form_values(self) -> tuple[str, str, str, str] | None:
        name = self.name_edit.text().strip()
        psp = self.psp_edit.text().strip()
        act_type = self.type_edit.text().strip()
        notes = self.notes_edit.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "Vorlage", "Bitte einen Namen eingeben.")
            return None
        if not psp and not act_type:
            QMessageBox.warning(self, "Vorlage", "Mindestens PSP oder Leistungsart muss gesetzt sein.")
            return None
        return name, psp, act_type, notes

    def _add_preset(self):
        values = self._get_form_values()
        if not values:
            return
        name, psp, act_type, notes = values
        try:
            self.db.add_preset(Preset(id=None, name=name, psp=psp, activity_type=act_type, notes=notes))
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Vorlage konnte nicht gespeichert werden:\n{e}")
            return
        self._refresh_list()
        self._clear_form()
        self.presets_changed.emit()

    def _update_preset(self):
        current = self.tree.currentItem()
        if current is None:
            return
        values = self._get_form_values()
        if not values:
            return
        name, psp, act_type, notes = values
        preset_id = current.data(0, Qt.UserRole)
        try:
            self.db.update_preset(Preset(id=preset_id, name=name, psp=psp, activity_type=act_type, notes=notes))
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Vorlage konnte nicht aktualisiert werden:\n{e}")
            return
        self._refresh_list()
        self.presets_changed.emit()

    def _delete_preset(self):
        current = self.tree.currentItem()
        if current is None:
            return
        preset_id = current.data(0, Qt.UserRole)
        reply = QMessageBox.question(
            self, "Löschen", f"Vorlage \"{current.text(0)}\" wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.delete_preset(preset_id)
            self._refresh_list()
            self._clear_form()
            self.presets_changed.emit()

    def _clear_form(self):
        self.name_edit.clear()
        self.psp_edit.clear()
        self.type_edit.clear()
        self.notes_edit.clear()
        self.tree.clearSelection()
        self.update_btn.setVisible(False)
        self.delete_btn.setVisible(False)
