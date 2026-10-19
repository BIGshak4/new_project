"""Small in-process caches for things that are the same on every request.

The database is remote; every round trip costs tens to hundreds of milliseconds. The
skill/tip id maps and the question content change only when content is (re)loaded,
so they are kept for a short while instead of being re-read on every action.

Instances are per process. `clear()` is for tests and for the seed loader.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable


class TTLCache[T]:
    def __init__(self, seconds: float, *, max_entries: int = 1024):
        if max_entries < 1:
            raise ValueError("a cache must have a positive entry limit")
        self.seconds = seconds
        self.max_entries = max_entries
        self._entries: OrderedDict[object, tuple[float, T]] = OrderedDict()
        self._generation = 0                 # bumped by invalidate(): a load that started before it must not store

    async def get(self, key: object, load: Callable[[], Awaitable[T]]) -> T:
        entry = self._entries.get(key)
        now = time.monotonic()
        if entry is not None and now - entry[0] < self.seconds:
            self._entries.move_to_end(key)
            return entry[1]
        generation = self._generation
        value = await load()
        if generation != self._generation:   # invalidated while loading (a member added, a question reloaded): serve, don't keep
            return value
        # A question ID is caller-controlled, including IDs that do not exist.
        # Expiry alone did not remove those entries: bound fresh misses as well
        # as discarding expired ones, so UUID churn cannot grow memory forever.
        now = time.monotonic()
        for old_key, (loaded_at, _) in list(self._entries.items()):
            if now - loaded_at >= self.seconds:
                self._entries.pop(old_key, None)
        self._entries[key] = (now, value)
        self._entries.move_to_end(key)
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)
        return value

    def peek(self, key: object) -> T | None:
        """The fresh value if there is one, without loading anything."""
        entry = self._entries.get(key)
        if entry is not None and time.monotonic() - entry[0] < self.seconds:
            self._entries.move_to_end(key)
            return entry[1]
        self._entries.pop(key, None)
        return None

    def invalidate(self, key: object | None = None) -> None:
        self._generation += 1
        if key is None:
            self._entries.clear()
        else:
            self._entries.pop(key, None)


# skill and tip ids never change once loaded; question content changes only on a content load
ID_MAPS: TTLCache[dict] = TTLCache(seconds=300)
QUESTIONS: TTLCache[object] = TTLCache(seconds=60)
# pilot access per user: a new member waits at most this long; a removed member keeps access at most this long
ACCESS: TTLCache[object] = TTLCache(seconds=120, max_entries=4096)


def clear() -> None:
    ID_MAPS.invalidate()
    QUESTIONS.invalidate()
    ACCESS.invalidate()
