"""Count unordered distinct-index pairs, retaining multiplicity of equal values."""
from collections.abc import Iterable


def count_pairs(values: Iterable[int], target: int) -> int:
    seen: dict[int, int] = {}
    total = 0
    for value in values:
        total += seen.get(target - value, 0)
        seen[value] = seen.get(value, 0) + 1
    return total
