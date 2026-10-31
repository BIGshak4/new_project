"""Equality-run solution; values may recur in separate or adjacent groups.

Contract: concatenate nonempty three-equal groups, then delete two elements
from one group. This accepts the resulting array and returns its damaged value.
Full run validation is optional robustness and does not infer global sorting.
"""


def damaged_value(values):
    n = len(values)
    if n == 0 or n % 3 != 1:
        raise ValueError('Expected a nonempty array of length 3*g-2')
    found = False
    answer = None
    start = 0
    while start < n:
        value = values[start]
        end = start + 1
        while end < n and values[end] == value:
            end += 1
        remainder = (end - start) % 3
        if remainder == 1:
            if found:
                raise ValueError('More than one damaged run')
            answer, found = value, True
        elif remainder != 0:
            raise ValueError('Invalid run length')
        start = end
    if not found:
        raise ValueError('No damaged run')
    return answer
