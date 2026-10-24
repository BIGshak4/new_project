"""PREP-041 C: n distinct values in 0..n, exactly one missing; read-only input.

The input validity promise is not fully validated. Flags use O(n) storage; XOR
uses O(1) machine words, not a fixed bit count for arbitrary n.
"""


def missing_one_with_flags(values):
    present = [False] * (len(values) + 1)
    for value in values:
        present[value] = True
    for value, found in enumerate(present):
        if not found:
            return value
    raise ValueError("valid input must omit exactly one domain value")


def missing_one_xor(values):
    missing = len(values)
    for index, value in enumerate(values):
        missing ^= index ^ value
    return missing
