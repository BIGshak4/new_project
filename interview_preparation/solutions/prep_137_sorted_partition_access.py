def boundary_random_access(values, key):
    """Return first index i with values[i] >= key, or len(values)."""
    lo, hi = 0, len(values)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if key > values[mid]:
            lo = mid + 1
        else:
            hi = mid
    return lo


def boundary_forward(values, key):
    """The iterable exposes the next cell only, in ascending index order."""
    consumed = 0
    for value in values:
        if not key > value:
            return consumed
        consumed += 1
    return consumed
