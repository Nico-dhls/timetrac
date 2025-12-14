import json
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import main


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
