"""PREP-040: distinct-index pair sum, with explicit time/space tradeoffs.

Inputs are unsorted integer sequences. None of these functions changes the input.
Hash-based bounds are expected/amortized, not worst-case guarantees.
"""

from collections.abc import Sequence


def has_pair_quadratic(values: Sequence[int], target: int) -> bool:
    """Try each pair of different positions: O(n^2) time, O(1) extra words."""
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] + values[j] == target:
                return True
    return False


def has_pair_sum(values: Sequence[int], target: int) -> bool:
    """Expected O(n) time and O(n) space under ordinary hash assumptions."""
    seen: set[int] = set()
    for value in values:
        if target - value in seen:
            return True
        seen.add(value)
    return False


def pair_sum_indices(values: Sequence[int], target: int) -> tuple[int, int] | None:
    """Optional extension: return any valid pair of indices, or None."""
    seen: dict[int, int] = {}
    for i, value in enumerate(values):
        complement = target - value
        if complement in seen:
            return seen[complement], i
        seen[value] = i
    return None


def has_pair_sum_sorted(values: Sequence[int], target: int) -> bool:
    """O(n log n) worst-case comparisons, O(n) auxiliary storage in this code.

    sorted() creates a copy, so original positions are not returned. The list
    copy and Python's sorting workspace must not be described as O(1) space.
    """
    ordered = sorted(values)
    left, right = 0, len(ordered) - 1
    while left < right:
        total = ordered[left] + ordered[right]
        if total == target:
            return True
        if total < target:
            left += 1
        else:
            right -= 1
    return False


if __name__ == "__main__":
    values = [4, 1, 7, 3]
    print(has_pair_sum(values, 8))
    print(pair_sum_indices(values, 8))
