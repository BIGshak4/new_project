"""Peak weighted demand under explicit endpoint conventions.

integer_inclusive means days start..end, both included.
continuous_half_open means [start,end); exact Fraction endpoints are supported.
Each demand is a nonnegative integer. Workers can be reassigned immediately.
"""
import math
from fractions import Fraction


def minimum_workers(intervals, *, mode="integer_inclusive"):
    if mode not in ("integer_inclusive", "continuous_half_open"):
        raise ValueError("unknown endpoint convention")
    events = {}
    for start, end, demand in intervals:
        if type(demand) is not int or demand < 0:
            raise ValueError("demand must be a nonnegative integer")
        if mode == "integer_inclusive":
            if type(start) is not int or type(end) is not int:
                raise ValueError("inclusive days must be integers")
        else:
            for value in (start, end):
                if type(value) not in (int, float, Fraction) or (type(value) is float and not math.isfinite(value)):
                    raise ValueError("endpoints must be finite real numbers")
        if start > end:
            raise ValueError("interval end precedes its start")
        release = end + 1 if mode == "integer_inclusive" else end
        if demand == 0 or start == release:
            continue
        events[start] = events.get(start, 0) + demand
        events[release] = events.get(release, 0) - demand
    active = peak = 0
    for moment in sorted(events):
        active += events[moment]
        peak = max(peak, active)
    return peak
