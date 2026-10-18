"""Find values removed from a permutation of 1..n.

Editorial interpretation: removed values are hidden, and only the remaining
entries are accessible. Values were initially unique. These are algorithmic
preconditions; this module does not validate arbitrary malformed input.
"""

from collections.abc import Sequence


def missing_one(remaining: Sequence[int], n: int = 100) -> int:
    """Return the one missing value in O(n) time and O(1) machine words.

    Preconditions: n >= 1 and remaining is a permutation of 1..n with one
    value removed. The size check alone does not verify that precondition.
    Python integer arithmetic is exact; fixed-width languages must avoid
    overflow when computing n * (n + 1) // 2.
    """
    if n < 1 or len(remaining) != n - 1:
        raise ValueError("Expected n >= 1 and exactly n - 1 remaining entries")
    return n * (n + 1) // 2 - sum(remaining)


def missing_two(remaining: Sequence[int], n: int = 100) -> tuple[int, int]:
    """Return the two distinct missing values in ascending order.

    Preconditions: n >= 2 and remaining is a permutation of 1..n with two
    distinct values removed. There are two passes over the input. The size
    check does not detect duplicates, out-of-range values, or other malformed
    input. O(n) time and O(1) words in the word-RAM model; O(log n) auxiliary
    bits if integer widths are counted.
    """
    if n < 2 or len(remaining) != n - 2:
        raise ValueError("Expected n >= 2 and exactly n - 2 remaining entries")

    combined = 0
    for value in range(1, n + 1):
        combined ^= value
    for value in remaining:
        combined ^= value

    # Every present value cancels. combined = missing_a XOR missing_b.
    # Distinct missing values imply combined != 0.
    distinguishing_bit = combined & -combined
    missing_a = 0
    missing_b = 0

    for value in range(1, n + 1):
        if value & distinguishing_bit:
            missing_a ^= value
        else:
            missing_b ^= value
    for value in remaining:
        if value & distinguishing_bit:
            missing_a ^= value
        else:
            missing_b ^= value

    if missing_a < missing_b:
        return missing_a, missing_b
    return missing_b, missing_a


if __name__ == "__main__":
    one_removed = [value for value in range(1, 101) if value != 37]
    two_removed = [value for value in range(1, 101) if value not in (37, 82)]
    print("One missing:", missing_one(one_removed))
    print("Two missing:", missing_two(two_removed))
