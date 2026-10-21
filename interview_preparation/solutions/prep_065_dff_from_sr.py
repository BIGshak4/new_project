"""Ideal same-clock active-high SR flip-flop model, not a transparent latch."""


def sr_edge(q: int, s: int, r: int, *, rising: bool = True) -> int:
    if any(type(v) is not int or v not in (0, 1) for v in (q, s, r)):
        raise ValueError("binary integer values required")
    if not rising:
        return q
    if s and r:
        raise ValueError("forbidden synchronous SR input")
    return 1 if s else 0 if r else q


def dff_from_sr(q: int, d: int, *, rising: bool = True) -> int:
    if type(d) is not int or d not in (0, 1):
        raise ValueError("binary D required")
    return sr_edge(q, d, 1 - d, rising=rising)
