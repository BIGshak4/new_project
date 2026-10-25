"""Missing values in 1..N; repeated input values and zero sentinels allowed.

The read-only construction accepts arbitrary finite input length L. The
constant-auxiliary-workspace variant requires exactly N-1 mutable entries.
Output storage is counted separately; it may itself contain N integers.
"""


def missing_all_flags(values, n):
    if type(n) is not int or n < 0:
        raise ValueError("N must be a nonnegative integer")
    seen = [False] * (n + 1)
    for value in values:
        if type(value) is not int or not 0 <= value <= n:
            raise ValueError("entries must be integers in 0..N")
        if value != 0:
            seen[value] = True
    return [value for value in range(1, n + 1) if not seen[value]]


def missing_all_inplace(values, n):
    if type(n) is not int or n < 1 or len(values) != n - 1:
        raise ValueError("mutable variant requires N>=1 and exactly N-1 entries")
    if any(type(value) is not int or not 0 <= value <= n for value in values):
        raise ValueError("entries must be integers in 0..N")
    final_present = False
    index = 0
    while index < len(values):
        value = values[index]
        if value == n:
            final_present = True
            index += 1
        elif 1 <= value < n and values[value - 1] != value:
            values[index], values[value - 1] = values[value - 1], value
        else:
            index += 1
    missing = [value for value in range(1, n) if values[value - 1] != value]
    if not final_present:
        missing.append(n)
    return missing
