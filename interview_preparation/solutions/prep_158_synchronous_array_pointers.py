"""Discrete synchronous visits versus continuous interpolation."""
from fractions import Fraction


def visits(size=100, left_start=2, right_start=98, left_step=2, right_step=3):
    if any(type(x) is not int for x in (size, left_start, right_start, left_step, right_step)):
        raise ValueError("integer labels and steps required")
    if size < 1 or left_step < 1 or right_step < 1:
        raise ValueError("positive size and steps required")
    if not (1 <= left_start <= size and 1 <= right_start <= size):
        raise ValueError("first visited positions must lie in the array")
    t = 0
    while True:
        left, right = left_start + left_step * t, right_start - right_step * t
        if not (1 <= left <= size and 1 <= right <= size):
            return
        yield t, left, right
        t += 1


def simultaneous_meeting(**kwargs):
    return next(((t, left) for t, left, right in visits(**kwargs) if left == right), None)


def continuous_intersection():
    """Additional assumption: linear travel between the stated tick positions."""
    t = Fraction(98 - 2, 2 + 3)
    return t, 2 + 2 * t
