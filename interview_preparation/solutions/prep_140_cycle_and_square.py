"""Finite, saturating cycle index and square; all updates use old state."""


def widths(limit):
    if type(limit) is not int or limit < 0:
        raise ValueError("N must be a nonnegative integer")
    return max(1, limit.bit_length()), max(1, (limit * limit).bit_length())


def step(n, square, limit, *, reset=False):
    widths(limit)
    if not (0 <= n <= limit and square == n * n):
        raise ValueError("State must satisfy 0 <= n <= N and square = n squared")
    if reset:
        return 0, 0
    if n == limit:
        return n, square
    # In gates, (n << 1) | 1 is the concatenation {n, 1}.
    odd_difference = (n << 1) | 1
    return n + 1, square + odd_difference


def trace(limit, cycles):
    widths(limit)
    if type(cycles) is not int or cycles < 0:
        raise ValueError("cycles must be nonnegative")
    n = square = 0
    result = [(n, square)]
    for _ in range(cycles):
        n, square = step(n, square, limit)
        result.append((n, square))
    return result
