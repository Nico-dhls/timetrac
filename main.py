"""TimeTrac - Time tracking for SAP ITP.

Legacy entry point - delegates to timetrac.app.main().
Also exposes functions needed by existing tests for backwards compatibility.
"""

import json
from datetime import datetime
from pathlib import Path

# Constants used by existing tests
DATA_FILE = Path("time_entries.json")
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
MAX_RECENTS = 10


def load_data():
    """Load data from JSON file (legacy format)."""
    if DATA_FILE.exists():
        try:
            raw = json.loads(DATA_FILE.read_text())
        except json.JSONDecodeError:
            return {"entries": {}, "presets": []}
        if "entries" in raw or "presets" in raw:
            raw.setdefault("entries", {})
            raw.setdefault("presets", [])
            return raw
        return {"entries": raw, "presets": []}
    return {"entries": {}, "presets": []}


def save_data(data):
    """Save data to JSON file (legacy format)."""
    DATA_FILE.write_text(json.dumps(data, indent=2))


def ensure_date_bucket(entries, day_key):
    if day_key not in entries:
        entries[day_key] = []
    return entries[day_key]


def parse_time(value):
    return datetime.strptime(value, TIME_FORMAT)


def calculate_hours(start_value, end_value):
    start_time = parse_time(start_value)
    end_time = parse_time(end_value)
    if end_time <= start_time:
        raise ValueError("Ende muss nach dem Start liegen")
    return (end_time - start_time).total_seconds() / 3600


def collect_recent_values(entries, field):
    values = []
    for day in sorted(entries.keys(), reverse=True):
        for entry in reversed(entries[day]):
            value = entry.get(field, "")
            if value and value not in values:
                values.append(value)
            if len(values) >= MAX_RECENTS:
                return values
    return values


def main():
    from timetrac.app import main as app_main
    app_main()


if __name__ == "__main__":
    main()
