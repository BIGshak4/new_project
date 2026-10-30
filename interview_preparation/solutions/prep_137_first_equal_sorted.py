"""First equal index in a promised nondecreasing integer sequence, or -1.

Input is read-only. Sortedness is a precondition, not a hidden linear scan.
"""


def first_equal(values, target):
    lo, hi = 0, len(values)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if values[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo if lo < len(values) and values[lo] == target else -1
