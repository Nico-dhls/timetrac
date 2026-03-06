"""SQLite database layer for TimeTrac."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import DaySummary, Preset, TimeEntry, TimeMode

DATE_FORMAT = "%Y-%m-%d"


def _app_data_dir() -> Path:
    """Return the platform-appropriate app data directory."""
    import sys

    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Roaming"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        import os
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    d = base / "TimeTrac"
    d.mkdir(parents=True, exist_ok=True)
    return d


def default_db_path() -> Path:
    return _app_data_dir() / "timetrac.db"


class Database:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or default_db_path()
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                psp TEXT NOT NULL DEFAULT '',
                activity_type TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                hours REAL NOT NULL,
                start_time TEXT NOT NULL DEFAULT '',
                end_time TEXT NOT NULL DEFAULT '',
                mode TEXT NOT NULL DEFAULT 'range',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(date);
            CREATE INDEX IF NOT EXISTS idx_entries_psp ON entries(psp);

            CREATE TABLE IF NOT EXISTS presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                psp TEXT NOT NULL DEFAULT '',
                activity_type TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                billable INTEGER NOT NULL DEFAULT 1
            );
        """)
        self.conn.commit()
        self._migrate()

    def _migrate(self):
        """Run schema migrations for existing databases."""
        cursor = self.conn.execute("PRAGMA table_info(presets)")
        columns = {row[1] for row in cursor.fetchall()}
        if "billable" not in columns:
            self.conn.execute("ALTER TABLE presets ADD COLUMN billable INTEGER NOT NULL DEFAULT 1")
            self.conn.commit()

    def close(self):
        self.conn.close()

    # --- Entries ---

    def _row_to_entry(self, row: tuple) -> TimeEntry:
        return TimeEntry(
            id=row[0],
            date=datetime.strptime(row[1], DATE_FORMAT).date(),
            psp=row[2],
            activity_type=row[3],
            description=row[4],
            hours=row[5],
            start_time=row[6],
            end_time=row[7],
            mode=TimeMode(row[8]),
            created_at=row[9],
        )

    def get_entries_for_date(self, day: date) -> list[TimeEntry]:
        cursor = self.conn.execute(
            "SELECT * FROM entries WHERE date = ? ORDER BY created_at",
            (day.strftime(DATE_FORMAT),),
        )
        return [self._row_to_entry(row) for row in cursor.fetchall()]

    def get_entries_for_week(self, day: date) -> dict[date, list[TimeEntry]]:
        start = day - timedelta(days=day.weekday())
        end = start + timedelta(days=6)
        cursor = self.conn.execute(
            "SELECT * FROM entries WHERE date BETWEEN ? AND ? ORDER BY date, created_at",
            (start.strftime(DATE_FORMAT), end.strftime(DATE_FORMAT)),
        )
        result: dict[date, list[TimeEntry]] = {}
        for i in range(7):
            result[start + timedelta(days=i)] = []
        for row in cursor.fetchall():
            entry = self._row_to_entry(row)
            result.setdefault(entry.date, []).append(entry)
        return result

    def add_entry(self, entry: TimeEntry) -> int:
        cursor = self.conn.execute(
            """INSERT INTO entries (date, psp, activity_type, description, hours,
               start_time, end_time, mode)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.date.strftime(DATE_FORMAT),
                entry.psp,
                entry.activity_type,
                entry.description,
                entry.hours,
                entry.start_time,
                entry.end_time,
                entry.mode.value,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_entry(self, entry: TimeEntry):
        self.conn.execute(
            """UPDATE entries SET date=?, psp=?, activity_type=?, description=?,
               hours=?, start_time=?, end_time=?, mode=? WHERE id=?""",
            (
                entry.date.strftime(DATE_FORMAT),
                entry.psp,
                entry.activity_type,
                entry.description,
                entry.hours,
                entry.start_time,
                entry.end_time,
                entry.mode.value,
                entry.id,
            ),
        )
        self.conn.commit()

    def delete_entry(self, entry_id: int):
        self.conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.conn.commit()

    def get_recent_values(self, field: str, limit: int = 15) -> list[str]:
        column_map = {
            "psp": "psp",
            "activity_type": "activity_type",
            "description": "description",
        }
        col = column_map.get(field)
        if not col:
            return []
        cursor = self.conn.execute(
            f"SELECT DISTINCT {col} FROM entries WHERE {col} != '' "
            f"ORDER BY date DESC, created_at DESC LIMIT ?",
            (limit,),
        )
        return [row[0] for row in cursor.fetchall()]

    def get_day_total(self, day: date) -> float:
        cursor = self.conn.execute(
            "SELECT COALESCE(SUM(hours), 0) FROM entries WHERE date = ?",
            (day.strftime(DATE_FORMAT),),
        )
        return cursor.fetchone()[0]

    def get_week_total(self, day: date) -> float:
        start = day - timedelta(days=day.weekday())
        end = start + timedelta(days=6)
        cursor = self.conn.execute(
            "SELECT COALESCE(SUM(hours), 0) FROM entries WHERE date BETWEEN ? AND ?",
            (start.strftime(DATE_FORMAT), end.strftime(DATE_FORMAT)),
        )
        return cursor.fetchone()[0]

    def get_week_summary(self, day: date) -> list[DaySummary]:
        week_entries = self.get_entries_for_week(day)
        summaries = []
        for d in sorted(week_entries.keys()):
            entries = week_entries[d]
            total = sum(e.hours for e in entries)
            summaries.append(DaySummary(date=d, total_hours=total, entries=entries))
        return summaries

    # --- Presets ---

    def _row_to_preset(self, row: tuple) -> Preset:
        return Preset(id=row[0], name=row[1], psp=row[2], activity_type=row[3], notes=row[4],
                       billable=bool(row[5]) if len(row) > 5 else True)

    def get_presets(self) -> list[Preset]:
        cursor = self.conn.execute("SELECT * FROM presets ORDER BY name")
        return [self._row_to_preset(row) for row in cursor.fetchall()]

    def add_preset(self, preset: Preset) -> int:
        cursor = self.conn.execute(
            "INSERT INTO presets (name, psp, activity_type, notes, billable) VALUES (?, ?, ?, ?, ?)",
            (preset.name, preset.psp, preset.activity_type, preset.notes, int(preset.billable)),
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_preset(self, preset: Preset):
        self.conn.execute(
            "UPDATE presets SET name=?, psp=?, activity_type=?, notes=?, billable=? WHERE id=?",
            (preset.name, preset.psp, preset.activity_type, preset.notes, int(preset.billable), preset.id),
        )
        self.conn.commit()

    def delete_preset(self, preset_id: int):
        self.conn.execute("DELETE FROM presets WHERE id = ?", (preset_id,))
        self.conn.commit()

    # --- Statistics ---

    def get_hours_by_psp(self, start: date, end: date) -> list[dict]:
        """Return hours grouped by PSP for a date range, with billable info from presets."""
        cursor = self.conn.execute(
            """SELECT e.psp, SUM(e.hours) as total_hours, e.activity_type
               FROM entries e
               WHERE e.date BETWEEN ? AND ?
               GROUP BY e.psp, e.activity_type
               ORDER BY total_hours DESC""",
            (start.strftime(DATE_FORMAT), end.strftime(DATE_FORMAT)),
        )
        results = []
        # Build a lookup of PSP -> billable from presets
        presets = {p.psp: p.billable for p in self.get_presets() if p.psp}
        for row in cursor.fetchall():
            psp = row[0]
            results.append({
                "psp": psp,
                "hours": row[1],
                "activity_type": row[2],
                "billable": presets.get(psp, True),
            })
        return results

    def get_hours_by_psp_merged(self, start: date, end: date) -> list[dict]:
        """Return hours grouped by PSP only (merging activity types), with billable info."""
        cursor = self.conn.execute(
            """SELECT e.psp, SUM(e.hours) as total_hours
               FROM entries e
               WHERE e.date BETWEEN ? AND ?
               GROUP BY e.psp
               ORDER BY total_hours DESC""",
            (start.strftime(DATE_FORMAT), end.strftime(DATE_FORMAT)),
        )
        presets = {p.psp: p.billable for p in self.get_presets() if p.psp}
        results = []
        for row in cursor.fetchall():
            psp = row[0]
            results.append({
                "psp": psp,
                "hours": row[1],
                "billable": presets.get(psp, True),
            })
        return results

    def get_daily_hours(self, start: date, end: date) -> list[dict]:
        """Return total hours per day in a date range."""
        cursor = self.conn.execute(
            """SELECT date, SUM(hours) FROM entries
               WHERE date BETWEEN ? AND ?
               GROUP BY date ORDER BY date""",
            (start.strftime(DATE_FORMAT), end.strftime(DATE_FORMAT)),
        )
        return [{"date": datetime.strptime(row[0], DATE_FORMAT).date(), "hours": row[1]}
                for row in cursor.fetchall()]

    # --- Migration from JSON ---

    def import_from_json(self, json_path: Path) -> int:
        """Import entries from old time_entries.json format. Returns count imported."""
        if not json_path.exists():
            return 0

        try:
            raw = json.loads(json_path.read_text())
        except (json.JSONDecodeError, OSError):
            return 0

        # Handle both formats: {entries: {...}, presets: [...]} and plain {date: [...]}
        if "entries" in raw:
            entries_data = raw.get("entries", {})
            presets_data = raw.get("presets", [])
        else:
            entries_data = raw
            presets_data = []

        count = 0
        for day_key, day_entries in entries_data.items():
            try:
                day = datetime.strptime(day_key, DATE_FORMAT).date()
            except ValueError:
                continue
            for entry_data in day_entries:
                hours = entry_data.get("hours", 0)
                if isinstance(hours, str):
                    try:
                        hours = float(hours.replace(",", "."))
                    except ValueError:
                        hours = 0
                mode = entry_data.get("mode", "range")
                entry = TimeEntry(
                    id=None,
                    date=day,
                    psp=entry_data.get("psp", ""),
                    activity_type=entry_data.get("type", ""),
                    description=entry_data.get("desc", ""),
                    hours=float(hours),
                    start_time=entry_data.get("start", ""),
                    end_time=entry_data.get("end", ""),
                    mode=TimeMode(mode) if mode in ("range", "duration") else TimeMode.RANGE,
                )
                self.add_entry(entry)
                count += 1

        for preset_data in presets_data:
            if isinstance(preset_data, dict):
                name = preset_data.get("name", "")
                if name:
                    try:
                        self.add_preset(Preset(
                            id=None,
                            name=name,
                            psp=preset_data.get("psp", ""),
                            activity_type=preset_data.get("type", ""),
                            notes="",
                        ))
                    except sqlite3.IntegrityError:
                        pass  # duplicate name

        return count
