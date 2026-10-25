"""Exact spatial flame-front simulation for positive piecewise burn densities.

Every segment has unit spatial length and its supplied one-end burn duration.
The local speed at either front is the reciprocal of that segment duration.
Fronts do not affect each other until meeting. Ignition is instantaneous.
"""

from fractions import Fraction
from math import ceil, floor


def burnout(profile, *, left=0, right=None):
    durations = tuple(Fraction(x) for x in profile)
    if not durations or any(x <= 0 for x in durations):
        raise ValueError("positive segment burn durations required")
    ignitions = [Fraction(x) for x in (left, right) if x is not None]
    if not ignitions or any(x < 0 for x in ignitions):
        raise ValueError("at least one nonnegative ignition time required")
    left_time = Fraction(left) if left is not None else None
    right_time = Fraction(right) if right is not None else None
    time, low, high = min(ignitions), Fraction(0), Fraction(len(durations))
    while low < high:
        left_speed = 1 / durations[floor(low)] if left_time is not None and time >= left_time else Fraction(0)
        right_speed = 1 / durations[ceil(high) - 1] if right_time is not None and time >= right_time else Fraction(0)
        candidates = []
        if left_speed:
            candidates.append((floor(low) + 1 - low) / left_speed)
        if right_speed:
            candidates.append((high - (ceil(high) - 1)) / right_speed)
        if left_speed + right_speed:
            candidates.append((high - low) / (left_speed + right_speed))
        candidates.extend(x - time for x in (left_time, right_time) if x is not None and x > time)
        step = min(candidates)
        assert step > 0
        low += left_speed * step
        high -= right_speed * step
        time += step
    assert low == high
    return time, low


def measure_three_quarters(profile_a, profile_b, *, b_start="left"):
    if sum(map(Fraction, profile_a)) != 60 or sum(map(Fraction, profile_b)) != 60:
        raise ValueError("each complete one-end burn time must be exactly sixty")
    if b_start not in ("left", "right"):
        raise ValueError("choose an endpoint")
    first_event, meeting_a = burnout(profile_a, left=0, right=0)
    starts = {"left": 0, "right": first_event} if b_start == "left" else {"left": first_event, "right": 0}
    final_event, meeting_b = burnout(profile_b, **starts)
    return {"first_burnout_minutes": first_event, "final_burnout_minutes": final_event,
            "meeting_a": meeting_a, "meeting_b": meeting_b}
