"""One shared puzzle per Jerusalem calendar day, drawn from alternate interview prompts."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
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
        starts = [
            entry.available_from for entry in self.entries
            if entry.start_puzzle_rotation and entry.available_from <= day
        ]
        entry = self._puzzle_rotation(day, max(starts)) if starts else self._family_rotation(day)
        self._current = (day, entry)
        return entry

    def _puzzle_rotation(self, day: date, start: date) -> DailyPuzzleEntry:
        previous = None
        if any(entry.available_from < start for entry in self.entries):
            previous = self.for_day(start - timedelta(days=1)).source_question_key
        first_deck = True
        while True:
            seed = f"daily-puzzle-deck:{start.isoformat()}:"
            remaining = sorted(
                (entry for entry in self.entries if entry.available_from <= start),
                key=lambda entry: hashlib.sha256((seed + entry.id).encode()).digest(),
            )
            if first_deck:
                # Put a new puzzle first on the first Jerusalem day of its rotation.
                first = next((
                    i for i, entry in enumerate(remaining)
                    if entry.available_from == start and entry.source_question_key != previous
                ), 0)
                remaining.insert(0, remaining.pop(first))
            deck_size = len(remaining)
            counts = Counter(entry.source_question_key for entry in remaining)
            for offset in range(deck_size):
                # If one family holds a majority of the remaining cards, alternate
                # it now so it does not form a run at the end of the deck.
                family, count = counts.most_common(1)[0]
                required = family if count * 2 > len(remaining) and family != previous else None
                index = next((
                    i for i, entry in enumerate(remaining)
                    if entry.source_question_key != previous
                    and (required is None or entry.source_question_key == required)
                ), 0)
                entry = remaining.pop(index)
                if (day - start).days == offset:
                    return entry
                previous = entry.source_question_key
                counts[previous] -= 1
            start += timedelta(days=deck_size)
            first_deck = False

    def _family_rotation(self, day: date) -> DailyPuzzleEntry:
        # Retain the original family schedule for its published calendar dates.
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
                return variants[round_number % len(variants)]
            previous = deck[-1]
            start += timedelta(days=len(deck))
            round_number += 1
        raise ApiError("temporarily_unavailable", "No daily puzzle is available yet.")

    def today(self, language: str) -> dict:
        return self.puzzle_on(self.clock().astimezone(ISRAEL).date(), language)

    def puzzle_on(self, day: date, language: str) -> dict:
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
