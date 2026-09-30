"""Fisher-Yates using the question's inclusive, one-based rand(m) contract."""
from collections.abc import Callable


def random_permutation(n: int, rand: Callable[[int], int]) -> list[int]:
    """Assume independent uniform draws; O(n) time, O(1) space beyond array."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError('n must be a nonnegative integer')
    values = list(range(1, n + 1))
    for i in range(n - 1):
        offset = rand(n - i)
        if not isinstance(offset, int) or not 1 <= offset <= n - i:
            raise ValueError('rand(m) must return an integer in [1, m]')
        j = i + offset - 1
        values[i], values[j] = values[j], values[i]
    return values


def print_random_permutation(n: int, rand: Callable[[int], int]) -> None:
    """Print without constructing a second list or a joined output string."""
    for value in random_permutation(n, rand):
        print(value)


def permutation_with_dict(n: int, rand: Callable[[int], int]):
    """Yield selected values using only a dictionary as the active bag.

    Expected O(n) time under constant expected hash-table operations,
    O(n) storage. Keys are one-based active positions, not used-value flags.
    """
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError('n must be a nonnegative integer')
    remaining = {i: i for i in range(1, n + 1)}
    m = n
    while m > 0:
        r = rand(m) if m > 1 else 1
        if not isinstance(r, int) or isinstance(r, bool) or not 1 <= r <= m:
            raise ValueError('rand(m) must return an integer in [1, m]')
        chosen = remaining[r]
        remaining[r] = remaining[m]
        del remaining[m]
        m -= 1
        yield chosen


def permutation_with_array(n: int, rand: Callable[[int], int]):
    """Yield from an array's shrinking prefix; O(n) time, O(n) storage."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError('n must be a nonnegative integer')
    values = list(range(1, n + 1))
    m = n
    while m > 0:
        r = rand(m) if m > 1 else 1
        if not isinstance(r, int) or isinstance(r, bool) or not 1 <= r <= m:
            raise ValueError('rand(m) must return an integer in [1, m]')
        j = r - 1
        chosen = values[j]
        values[j], values[m - 1] = values[m - 1], values[j]
        m -= 1
        yield chosen
