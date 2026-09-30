"""Optimal worst-case two-ball threshold search; threshold N+1 means none break."""


def min_drops(floors: int) -> int:
    if not isinstance(floors, int) or isinstance(floors, bool) or floors < 0:
        raise ValueError('floors must be a nonnegative integer')
    drops, capacity = 0, 0
    while capacity < floors:
        drops += 1
        capacity += drops
    return drops


def find_threshold(floors: int, breaks):
    """breaks(floor) is a stable monotone test shared by two identical balls.

    Returns (first breaking floor, trace); floors+1 means no breaking floor.
    The trace is for explanation/testing, not required by the strategy.
    """
    remaining = min_drops(floors)
    safe = 0
    trace = []
    while safe < floors:
        tested = min(safe + remaining, floors)
        broken = bool(breaks(tested))
        trace.append((1, tested, broken))
        remaining -= 1
        if broken:
            for candidate in range(safe + 1, tested):
                broken = bool(breaks(candidate))
                trace.append((2, candidate, broken))
                if broken:
                    return candidate, trace
            return tested, trace
        safe = tested
    return floors + 1, trace
