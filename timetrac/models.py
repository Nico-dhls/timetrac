"""Data models for TimeTrac."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum


class TimeMode(Enum):
    RANGE = "range"
    DURATION = "duration"


@dataclass
class TimeEntry:
    id: int | None
    date: date
    psp: str
    activity_type: str
    description: str
    hours: float
    start_time: str  # HH:MM or empty
    end_time: str  # HH:MM or empty
    mode: TimeMode
    created_at: str = ""

    @property
    def hours_display(self) -> str:
        return f"{self.hours:.2f}"


@dataclass
class Preset:
    id: int | None
    name: str
    psp: str
    activity_type: str
    notes: str = ""  # customer-specific notes / syntax hints for descriptions

    @property
    def display_name(self) -> str:
        parts = [self.name]
        if self.psp:
            parts.append(f"({self.psp})")
        return " ".join(parts)


@dataclass
class DaySummary:
    date: date
    total_hours: float
    entries: list[TimeEntry] = field(default_factory=list)
