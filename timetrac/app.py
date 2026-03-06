"""Application entry point for TimeTrac."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .database import Database
from .main_window import MainWindow
from .theme import apply_theme


def _try_migrate_json(db: Database):
    """Auto-import old time_entries.json if database is empty."""
    # Only migrate if DB has no entries yet
    cursor = db.conn.execute("SELECT COUNT(*) FROM entries")
    if cursor.fetchone()[0] > 0:
        return

    # Look for JSON in common locations
    candidates = [
        Path.cwd() / "time_entries.json",
        Path(__file__).resolve().parent.parent / "time_entries.json",
    ]
    for json_path in candidates:
        if json_path.exists():
            count = db.import_from_json(json_path)
            if count > 0:
                print(f"Migrated {count} entries from {json_path}")
            break


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TimeTrac")
    app.setOrganizationName("NicoDahlhaus")

    apply_theme(app)

    db = Database()
    _try_migrate_json(db)

    window = MainWindow(db)
    window.show()

    exit_code = app.exec()
    db.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
