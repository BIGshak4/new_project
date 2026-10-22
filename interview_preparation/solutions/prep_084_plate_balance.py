"""Ideal horizontal balance: fixed hooks versus an explicitly added free-placement variant."""
from itertools import combinations
from math import cos, pi, sin


def zero_added_moment(points):
    """Equal positive masses, horizontal coordinates about a centered ideal pivot.

    Integers/Fractions are exact. Floating coordinates need a stated tolerance
    outside this predicate. Zero moment is not a claim of stable equilibrium.
    """
    total_x = total_y = 0
    for x, y in points:
        total_x += x
        total_y += y
    return total_x == 0 and total_y == 0


def balanced_subsets(hooks, count):
    """Enumerate distinct fixed hooks, one equal mass per chosen hook.

    O(binomial(m, count) * count) arithmetic, O(count) working space apart
    from yielded answers. Exponential in m in the worst case; not a claim of
    an efficient general subset solver. Hook coordinates are required.
    """
    if count < 0 or count > len(hooks):
        raise ValueError("count must lie between zero and the number of hooks")
    for chosen in combinations(range(len(hooks)), count):
        if zero_added_moment([hooks[index] for index in chosen]):
            yield chosen


def regular_positions(count, radius=1.0):
    """Free distinct positions on one circle; added variant, not source geometry."""
    if count < 2 or radius <= 0:
        raise ValueError("at least two masses and a positive radius are required")
    return [(radius * cos(2 * pi * index / count),
             radius * sin(2 * pi * index / count)) for index in range(count)]
