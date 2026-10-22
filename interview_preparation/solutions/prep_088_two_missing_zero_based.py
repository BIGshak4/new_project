"""PREP-088: two omitted values, no auxiliary array, no input mutation.

Promise: values is a repeatable sequence of n distinct integers in 0..n+1.
Exactly two domain values are absent. Validation of that promise is not included.
Cost: O(n) word operations and O(1) auxiliary machine words, not constant bits.
"""
from collections.abc import Sequence


def missing_two_zero_based(values: Sequence[int]) -> tuple[int, int]:
    combined = 0
    for value in range(len(values) + 2):
        combined ^= value
    for value in values:
        combined ^= value
    split_bit = combined & -combined
    first = second = 0
    for value in range(len(values) + 2):
        if value & split_bit:
            first ^= value
        else:
            second ^= value
    for value in values:
        if value & split_bit:
            first ^= value
        else:
            second ^= value
    return (first, second) if first < second else (second, first)
