"""Small in-process caches for things that are the same on every request.

The database is remote; every round trip costs tens to hundreds of milliseconds. The
skill/tip id maps and the question content change only when content is (re)loaded,
so they are kept for a short while instead of being re-read on every action.

Instances are per process. `clear()` is for tests and for the seed loader.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable


class TTLCache[T]:
    def __init__(self, seconds: float):
        self.seconds = seconds
        self._entries: dict[object, tuple[float, T]] = {}

    async def get(self, key: object, load: Callable[[], Awaitable[T]]) -> T:
        entry = self._entries.get(key)
        now = time.monotonic()
        if entry is not None and now - entry[0] < self.seconds:
            return entry[1]
        value = await load()
        self._entries[key] = (now, value)
        return value

    def invalidate(self, key: object | None = None) -> None:
        if key is None:
            self._entries.clear()
        else:
            self._entries.pop(key, None)


# skill and tip ids never change once loaded; question content changes only on a content load
ID_MAPS: TTLCache[dict] = TTLCache(seconds=300)
QUESTIONS: TTLCache[object] = TTLCache(seconds=60)


def clear() -> None:
    ID_MAPS.invalidate()
    QUESTIONS.invalidate()
