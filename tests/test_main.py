"""Tests for legacy main.py compatibility and new database layer."""

import json
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import main
from timetrac.database import Database
from timetrac.models import Preset, TimeEntry, TimeMode


# --- Legacy main.py tests (backwards compatibility) ---


def test_load_data_default_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_FILE", tmp_path / "missing.json")
    assert main.load_data() == {"entries": {}, "presets": []}


def test_load_data_handles_invalid_json(tmp_path, monkeypatch):
    data_file = tmp_path / "data.json"
    data_file.write_text("not-json")
    monkeypatch.setattr(main, "DATA_FILE", data_file)
    assert main.load_data() == {"entries": {}, "presets": []}


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    data = {"entries": {"2024-01-01": [{"project": "X"}]}, "presets": ["A"]}
    data_file = tmp_path / "data.json"
    monkeypatch.setattr(main, "DATA_FILE", data_file)

    main.save_data(data)
    assert json.loads(data_file.read_text()) == data
    assert main.load_data() == data


def test_ensure_date_bucket_creates_and_returns_list():
    entries = {}
    bucket = main.ensure_date_bucket(entries, "2024-01-01")
    assert bucket == []
    assert entries == {"2024-01-01": []}


def test_parse_time_returns_datetime():
    parsed = main.parse_time("08:15")
    assert isinstance(parsed, datetime)
    assert parsed.hour == 8 and parsed.minute == 15


def test_calculate_hours_valid_range():
    assert main.calculate_hours("08:00", "09:30") == 1.5


def test_calculate_hours_raises_on_invalid_range():
    try:
        main.calculate_hours("10:00", "09:00")
    except ValueError:
        pass
    else:
        raise AssertionError("calculate_hours should raise when end is before start")


def test_collect_recent_values_limit_and_uniqueness():
    entries = {
        "2024-01-01": [
            {"description": "A"},
            {"description": "B"},
        ],
        "2024-01-02": [
            {"description": "B"},
            {"description": "C"},
        ],
    }

    values = main.collect_recent_values(entries, "description")
    assert values == ["C", "B", "A"]
    assert len(values) <= main.MAX_RECENTS


# --- New database layer tests ---


def _make_db(tmp_path) -> Database:
    return Database(tmp_path / "test.db")


def test_db_add_and_get_entry(tmp_path):
    db = _make_db(tmp_path)
    entry = TimeEntry(
        id=None,
        date=date(2024, 6, 15),
        psp="PSP-001",
        activity_type="Entwicklung",
        description="Feature X",
        hours=2.5,
        start_time="08:00",
        end_time="10:30",
        mode=TimeMode.RANGE,
    )
    entry_id = db.add_entry(entry)
    assert entry_id is not None

    entries = db.get_entries_for_date(date(2024, 6, 15))
    assert len(entries) == 1
    assert entries[0].psp == "PSP-001"
    assert entries[0].hours == 2.5
    assert entries[0].mode == TimeMode.RANGE
    db.close()


def test_db_update_entry(tmp_path):
    db = _make_db(tmp_path)
    entry = TimeEntry(
        id=None, date=date(2024, 1, 1), psp="A", activity_type="Dev",
        description="Test", hours=1.0, start_time="", end_time="",
        mode=TimeMode.DURATION,
    )
    entry_id = db.add_entry(entry)

    entry.id = entry_id
    entry.hours = 3.0
    entry.psp = "B"
    db.update_entry(entry)

    entries = db.get_entries_for_date(date(2024, 1, 1))
    assert len(entries) == 1
    assert entries[0].hours == 3.0
    assert entries[0].psp == "B"
    db.close()


def test_db_delete_entry(tmp_path):
    db = _make_db(tmp_path)
    entry = TimeEntry(
        id=None, date=date(2024, 1, 1), psp="A", activity_type="Dev",
        description="Test", hours=1.0, start_time="", end_time="",
        mode=TimeMode.DURATION,
    )
    entry_id = db.add_entry(entry)
    db.delete_entry(entry_id)

    entries = db.get_entries_for_date(date(2024, 1, 1))
    assert len(entries) == 0
    db.close()


def test_db_day_and_week_totals(tmp_path):
    db = _make_db(tmp_path)
    monday = date(2024, 6, 10)
    tuesday = date(2024, 6, 11)

    db.add_entry(TimeEntry(
        id=None, date=monday, psp="A", activity_type="Dev",
        description="", hours=4.0, start_time="", end_time="",
        mode=TimeMode.DURATION,
    ))
    db.add_entry(TimeEntry(
        id=None, date=tuesday, psp="A", activity_type="Dev",
        description="", hours=3.0, start_time="", end_time="",
        mode=TimeMode.DURATION,
    ))

    assert db.get_day_total(monday) == 4.0
    assert db.get_day_total(tuesday) == 3.0
    assert db.get_week_total(monday) == 7.0
    assert db.get_week_total(tuesday) == 7.0
    db.close()


def test_db_presets_crud(tmp_path):
    db = _make_db(tmp_path)
    preset = Preset(id=None, name="Test", psp="PSP-1", activity_type="Dev", notes="Use format: [TICKET]-desc")
    preset_id = db.add_preset(preset)

    presets = db.get_presets()
    assert len(presets) == 1
    assert presets[0].name == "Test"
    assert presets[0].notes == "Use format: [TICKET]-desc"

    preset.id = preset_id
    preset.notes = "Updated notes"
    db.update_preset(preset)

    presets = db.get_presets()
    assert presets[0].notes == "Updated notes"

    db.delete_preset(preset_id)
    assert len(db.get_presets()) == 0
    db.close()


def test_db_recent_values(tmp_path):
    db = _make_db(tmp_path)
    for i, psp in enumerate(["A", "B", "A", "C"]):
        db.add_entry(TimeEntry(
            id=None, date=date(2024, 1, 1 + i), psp=psp, activity_type="Dev",
            description="", hours=1.0, start_time="", end_time="",
            mode=TimeMode.DURATION,
        ))

    recent = db.get_recent_values("psp")
    assert "A" in recent
    assert "B" in recent
    assert "C" in recent
    db.close()


def test_db_week_summary(tmp_path):
    db = _make_db(tmp_path)
    monday = date(2024, 6, 10)
    db.add_entry(TimeEntry(
        id=None, date=monday, psp="A", activity_type="Dev",
        description="", hours=8.0, start_time="", end_time="",
        mode=TimeMode.DURATION,
    ))

    summary = db.get_week_summary(monday)
    assert len(summary) == 7
    assert summary[0].total_hours == 8.0
    assert summary[1].total_hours == 0.0
    db.close()


def test_db_import_from_json(tmp_path):
    json_path = tmp_path / "time_entries.json"
    data = {
        "entries": {
            "2024-01-15": [
                {"psp": "PSP-1", "type": "Dev", "desc": "Work", "hours": 2.0,
                 "start": "08:00", "end": "10:00", "mode": "range"},
            ]
        },
        "presets": [
            {"name": "Preset1", "psp": "PSP-1", "type": "Dev"},
        ],
    }
    json_path.write_text(json.dumps(data))

    db = _make_db(tmp_path)
    count = db.import_from_json(json_path)
    assert count == 1

    entries = db.get_entries_for_date(date(2024, 1, 15))
    assert len(entries) == 1
    assert entries[0].psp == "PSP-1"
    assert entries[0].activity_type == "Dev"

    presets = db.get_presets()
    assert len(presets) == 1
    assert presets[0].name == "Preset1"
    db.close()


def test_db_entries_for_week(tmp_path):
    db = _make_db(tmp_path)
    monday = date(2024, 6, 10)
    wednesday = date(2024, 6, 12)

    db.add_entry(TimeEntry(
        id=None, date=monday, psp="A", activity_type="Dev",
        description="Mon work", hours=4.0, start_time="", end_time="",
        mode=TimeMode.DURATION,
    ))
    db.add_entry(TimeEntry(
        id=None, date=wednesday, psp="A", activity_type="Dev",
        description="Wed work", hours=6.0, start_time="", end_time="",
        mode=TimeMode.DURATION,
    ))

    week = db.get_entries_for_week(wednesday)
    assert len(week[monday]) == 1
    assert len(week[wednesday]) == 1
    assert week[monday][0].description == "Mon work"
    db.close()
