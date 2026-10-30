"""Pairwise min/max with exactly ceil(3*n/2)-2 comparisons for n >= 1.

less(a,b) is one order comparison. Its implementation must not hide extra
element comparisons if the stated count is to model it. Duplicates work.
"""


def minmax_pairwise(values, less=None):
    if len(values) == 0:
        raise ValueError("empty input has no minimum or maximum")
    if less is None:
        def less(left, right):
            return left < right
    n = len(values)
    if n % 2:
        minimum = maximum = values[0]
        index = 1
    else:
        if less(values[0], values[1]):
            minimum, maximum = values[0], values[1]
        else:
            minimum, maximum = values[1], values[0]
        index = 2
    while index < n:
        if less(values[index], values[index + 1]):
            small, large = values[index], values[index + 1]
        else:
            small, large = values[index + 1], values[index]
        if less(small, minimum):
            minimum = small
        if less(maximum, large):
            maximum = large
        index += 2
    return minimum, maximum
