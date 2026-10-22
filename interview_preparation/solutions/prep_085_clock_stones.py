"""Exact equal-mass moment sums for twelve fixed hour marks on one circle."""
from itertools import combinations_with_replacement

# Twice each unit-radius coordinate in Q(sqrt(3)):
# (x_rational, x_sqrt3, y_rational, y_sqrt3). 12 is up; hours grow clockwise.
HOUR_VECTORS = {
    12: (0, 0, 2, 0), 1: (1, 0, 0, 1), 2: (0, 1, 1, 0),
    3: (2, 0, 0, 0), 4: (0, 1, -1, 0), 5: (1, 0, 0, -1),
    6: (0, 0, -2, 0), 7: (-1, 0, 0, -1), 8: (0, -1, -1, 0),
    9: (-2, 0, 0, 0), 10: (0, -1, 1, 0), 11: (-1, 0, 0, 1),
}


def moment_signature(hours):
    """Four integers; all zero iff the added horizontal center of mass is zero."""
    values = [0, 0, 0, 0]
    for hour in hours:
        if hour not in HOUR_VECTORS:
            raise ValueError("hour must be one of 1 through 12")
        for axis, value in enumerate(HOUR_VECTORS[hour]):
            values[axis] += value
    return tuple(values)


def balanced_placements(count=5):
    """All unordered placements, stacking allowed, with exact zero added moment.

    O(binomial(count+11,11) * count) arithmetic; O(count) enumeration storage
    apart from answers. The interview construction itself needs no search.
    """
    if count < 0:
        raise ValueError("stone count cannot be negative")
    for hours in combinations_with_replacement(range(1, 13), count):
        if moment_signature(hours) == (0, 0, 0, 0):
            yield hours


def example():
    """An equilateral triangle plus a diametrically opposite pair."""
    return (12, 4, 8, 3, 9)
