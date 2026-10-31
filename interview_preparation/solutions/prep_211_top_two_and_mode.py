"""Nonmutating algorithms for an unsorted array of integers of unknown range."""


def top_two_distinct(values):
    """Return ((largest, count), (second_distinct, count)); missing = None."""
    first = second = None
    first_count = second_count = 0
    for value in values:
        if first is not None and value == first:
            first_count += 1
        elif first is None or value > first:
            second, second_count = first, first_count
            first, first_count = value, 1
        elif second is not None and value == second:
            second_count += 1
        elif second is None or value > second:
            second, second_count = value, 1
    return ((first, first_count) if first is not None else None,
            (second, second_count) if second is not None else None)


def mode_with_count(values):
    """Return (mode, frequency), ties resolved to the smallest integer; empty=None."""
    counts = {}
    best = None
    best_count = 0
    for value in values:
        count = counts.get(value, 0) + 1
        counts[value] = count
        if count > best_count or (count == best_count and (best is None or value < best)):
            best, best_count = value, count
    return (best, best_count) if best is not None else None
