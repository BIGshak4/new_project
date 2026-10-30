"""Exact equal-distance trip arithmetic with finite positive quantities."""
from fractions import Fraction


def round_trip_average(distance, outbound_speed, return_speed):
    d, v1, v2 = map(Fraction, (distance, outbound_speed, return_speed))
    if d <= 0 or v1 <= 0 or v2 <= 0:
        raise ValueError("positive distance and finite positive speeds required")
    return 2 * d / (d / v1 + d / v2)


def return_speed_for_ratio(outbound_speed, ratio):
    """Target average = ratio * outbound_speed; require 0 < ratio < 2."""
    v1, r = map(Fraction, (outbound_speed, ratio))
    if v1 <= 0 or not 0 < r < 2:
        raise ValueError("a finite positive return speed needs 0 < ratio < 2")
    return r * v1 / (2 - r)
