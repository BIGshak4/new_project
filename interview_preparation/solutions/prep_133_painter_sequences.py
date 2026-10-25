"""Conditional painter models; the supplied prefixes do not determine a rule."""

from fractions import Fraction


def specified_positions(day):
    """One explicitly chosen continuation, day zero is the first painting day.

    This treats 0 and 100 as positions after clarifying the source's numbering;
    it does not claim that the inclusive range has only one hundred doors.
    """
    if type(day) is not int or day < 0:
        raise ValueError("Day must be a nonnegative integer")
    return 2 * day, 100 - day * (day + 3) // 2


def simultaneous_painted_door(days=14):
    return [
        (day, a) for day in range(days) for a, b in [specified_positions(day)] if a == b and 0 <= a <= 100
    ]


def first_crossing():
    """Conditional constant-speed motion between the day11/day12 positions."""
    left, right = specified_positions(11)
    next_left, next_right = specified_positions(12)
    fraction = Fraction(right - left, (next_left - left) + (right - next_right))
    return Fraction(11) + fraction, Fraction(left) + fraction * (next_left - left)


def two_compatible_continuations():
    """Both match all supplied prefix observations, with one paint per day."""
    a = [0, 2, 4, 6, 8]
    no_meeting = [100, 98, 95, 91, 86]
    meeting = [100, 98, 95, 90, 8]
    return a, no_meeting, meeting
