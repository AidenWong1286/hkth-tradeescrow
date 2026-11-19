"""Deterministic simulation clock (logical business time, Asia/Hong_Kong)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

HKT = timezone(timedelta(hours=8))
DEFAULT_START = datetime(2026, 11, 2, 9, 0, 0, tzinfo=HKT)


class SimClock:
    """Logical clock. Never reads wall-clock time, so every run is reproducible."""

    def __init__(self, start: datetime | str | None = None):
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        self._now = start or DEFAULT_START

    def now(self) -> datetime:
        return self._now

    def iso(self) -> str:
        return self._now.isoformat()

    def advance(self, hours: float = 0, minutes: float = 0, days: float = 0) -> str:
        self._now = self._now + timedelta(days=days, hours=hours, minutes=minutes)
        return self.iso()

    def set(self, value: datetime | str) -> None:
        self._now = datetime.fromisoformat(value) if isinstance(value, str) else value


def parse(ts: str | None) -> datetime | None:
    return datetime.fromisoformat(ts) if ts else None
