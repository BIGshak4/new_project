"""Mutate a list of integers in place; return its first absent positive integer."""


def first_missing_positive(values):
    if not isinstance(values, list) or any(type(v) is not int for v in values):
        raise ValueError('a mutable list of integers is required')
    n = len(values)
    for i in range(n):
        while 1 <= values[i] <= n and values[values[i] - 1] != values[i]:
            target = values[i] - 1
            values[i], values[target] = values[target], values[i]
    for i, value in enumerate(values):
        if value != i + 1:
            return i + 1
    return n + 1
