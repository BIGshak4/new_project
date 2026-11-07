"""Ideal concentric supported rope; chosen cat effective height is 0.25 m."""
from math import isfinite, pi


def rope_clearance(extra_length=2.0, effective_height=0.25):
    for value in (extra_length, effective_height):
        if type(value) not in (int, float) or not isfinite(value) or value < 0:
            raise ValueError('lengths must be finite nonnegative real numbers')
    gap = extra_length / (2 * pi)
    return {'gap_metres': gap, 'fits': effective_height <= gap,
            'margin_metres': gap - effective_height}
