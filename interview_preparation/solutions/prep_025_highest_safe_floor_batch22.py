"""Two reusable-until-broken eggs: return the highest safe floor, including N.

breaks(f) is deterministic and monotone. Floor zero is safe. Unless explicitly
known otherwise, floor N may also be safe. Optional trace belongs to the caller.
"""
from math import isqrt


def minimum_drops(floors: int, *, top_known_breaking: bool = False) -> int:
    if type(floors) is not int or floors < 0:
        raise ValueError("floors must be a nonnegative integer")
    if top_known_breaking and floors == 0:
        raise ValueError("a known breaking top needs at least one floor")
    unknown = floors - int(top_known_breaking)
    budget = (isqrt(1 + 8 * unknown) - 1) // 2
    return budget + int(budget * (budget + 1) // 2 < unknown)


def highest_safe_floor(floors: int, breaks, *, top_known_breaking: bool = False, trace=None) -> int:
    budget = minimum_drops(floors, top_known_breaking=top_known_breaking)
    upper = floors if top_known_breaking else floors + 1
    safe = 0

    def drop(egg, floor):
        broken = bool(breaks(floor))
        if trace is not None:
            trace.append((egg, floor, broken))
        return broken

    while upper - safe > 1:
        tested = min(safe + budget, upper - 1)
        budget -= 1
        if drop(1, tested):
            for candidate in range(safe + 1, tested):
                if drop(2, candidate):
                    return candidate - 1
            return tested - 1
        safe = tested
    return safe
