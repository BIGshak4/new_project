"""One shared puzzle per Jerusalem calendar day, drawn from alternate interview prompts."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from functools import cached_property
from zoneinfo import ZoneInfo

from app.api.errors import ApiError
from app.services.daily_puzzle_bank import DailyPuzzleEntry

ISRAEL = ZoneInfo("Asia/Jerusalem")


class DailyPuzzleService:
    def __init__(self, load_bank: Callable[[], tuple[DailyPuzzleEntry, ...]], clock: Callable[[], datetime] | None = None):
        self._load_bank = load_bank
        self._current: tuple[date, DailyPuzzleEntry] | None = None
        self.clock = clock or (lambda: datetime.now(UTC))

    @cached_property
    def entries(self) -> tuple[DailyPuzzleEntry, ...]:
        return tuple(sorted(self._load_bank(), key=lambda entry: entry.id))

    def for_day(self, day: date) -> DailyPuzzleEntry:
        current = self._current
        if current is not None and current[0] == day:
            return current[1]
        # A deck visits each source question once. New batches enter on the next shuffle,
        # so publishing more variants cannot change a puzzle people already opened.
        start = min((entry.available_from for entry in self.entries), default=None)
        previous = None
        round_number = 0
        while start is not None and start <= day:
            groups = defaultdict(list)
            for entry in self.entries:
                if entry.available_from <= start:
                    groups[entry.source_question_key].append(entry)
            seed = f"daily-puzzle:{start.isoformat()}:"
            deck = sorted(groups, key=lambda key: hashlib.sha256((seed + key).encode()).digest())
            if len(deck) > 1 and deck[0] == previous:
                deck[0], deck[1] = deck[1], deck[0]
            index = (day - start).days
            if index < len(deck):
                variants = groups[deck[index]]
                entry = variants[round_number % len(variants)]
                self._current = (day, entry)
                return entry
            previous = deck[-1]
            start += timedelta(days=len(deck))
            round_number += 1
        raise ApiError("temporarily_unavailable", "No daily puzzle is available yet.")

    def today(self, language: str) -> dict:
        day = self.clock().astimezone(ISRAEL).date()
        entry = self.for_day(day)
        return {
            "day": day,
            "expires_at": datetime.combine(day + timedelta(days=1), time.min, tzinfo=ISRAEL),
            "id": entry.id,
            "title": entry.title[language],
            "prompt": entry.prompt[language],
            "subject": entry.subject,
        }

    def reveal(self, day: date, puzzle_id: str, language: str) -> dict:
        if self.clock().astimezone(ISRAEL).date() != day:
            raise ApiError("conflict", "A new daily puzzle is available. Load it to continue.")
        entry = self.for_day(day)
        if entry.id != puzzle_id:
            raise ApiError("conflict", "This is no longer the current daily puzzle.")
        return {"day": day, "id": entry.id, "solution": entry.solution[language]}
