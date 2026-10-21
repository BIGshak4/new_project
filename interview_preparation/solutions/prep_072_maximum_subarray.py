"""Nonempty maximum contiguous subarray; inclusive zero-based boundaries.

Exact integers. Empty input returns None. Ties choose earliest start and then
earliest end. Returns (sum, start, end), without allocating the output slice.
"""


def maximum_subarray(values):
    if not values:
        return None
    current = best = values[0]
    start = best_start = best_end = 0
    for end in range(1, len(values)):
        # Equality extends: an earlier start wins tied sums.
        if current < 0:
            current, start = values[end], end
        else:
            current += values[end]
        if current > best or (current == best and start < best_start):
            best, best_start, best_end = current, start, end
    return best, best_start, best_end
