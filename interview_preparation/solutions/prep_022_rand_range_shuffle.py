"""Shuffle the supplied array in place using inclusive rand_range(min, max)."""
from collections.abc import Callable, MutableSequence


def shuffle_in_place(values: MutableSequence[int], rand_range: Callable[[int, int], int]) -> None:
    """O(n) swaps and O(1) auxiliary words; uniform if bounded draws are conditionally uniform."""
    for i in range(len(values) - 1, 0, -1):
        j = rand_range(0, i)
        if not isinstance(j, int) or isinstance(j, bool) or not 0 <= j <= i:
            raise ValueError("rand_range(min, max) must return an integer within both inclusive bounds")
        values[i], values[j] = values[j], values[i]
