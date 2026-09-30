"""Count ordered 1/2-step paths from level zero to level n, exactly."""


def _validate(n):
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError('n must be a nonnegative integer')


def count_ways(n: int) -> int:
    """Linear arithmetic-operation count, two running count values."""
    _validate(n)
    previous, current = 1, 1  # W(0), W(1)
    if n == 0:
        return previous
    for _ in range(2, n + 1):
        previous, current = current, previous + current
    return current


def count_ways_fast(n: int) -> int:
    """Return F(n+1) by iterative doubling: O(log n) big-integer operations."""
    _validate(n)
    a, b = 0, 1  # F(k), F(k+1), initially k=0
    for bit in bin(n + 1)[2:]:
        c = a * (2 * b - a)   # F(2k)
        d = a * a + b * b     # F(2k+1)
        if bit == '0':
            a, b = c, d
        else:
            a, b = d, c + d
    return a
