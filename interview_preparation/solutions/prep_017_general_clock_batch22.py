"""Minor angle of a conventional continuously moving twelve-hour clock."""
from fractions import Fraction


def hand_positions(hour: int, minute: int) -> tuple[Fraction, Fraction]:
    if type(hour) is not int or type(minute) is not int:
        raise TypeError("hour and minute must be integers")
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("hour 0..23 and minute 0..59 required")
    return Fraction(30 * (hour % 12)) + Fraction(minute, 2), Fraction(6 * minute)


def minor_angle(hour: int, minute: int) -> Fraction:
    hour_position, minute_position = hand_positions(hour, minute)
    clockwise_delta = (hour_position - minute_position) % 360
    return min(clockwise_delta, 360 - clockwise_delta)
