"""Josephus step 2, labels 1..n, with 1 removing 2 first."""
from collections import deque


def survivor(n: int) -> int:
    if n < 1:
        raise ValueError('n must be a positive integer')
    power = 1 << (n.bit_length() - 1)
    return 2 * (n - power) + 1


def survivor_with_loop(n: int) -> int:
    """Equivalent teaching version: find the largest power of two <= n."""
    if n < 1:
        raise ValueError('n must be a positive integer')
    power = 1
    while power * 2 <= n:
        power *= 2
    return 2 * (n - power) + 1


def simulate(n: int):
    """Return removal order and survivor, preserving the source's turn order."""
    if n < 1:
        raise ValueError('n must be a positive integer')
    circle = deque(range(1, n + 1))
    removed = []
    while len(circle) > 1:
        circle.rotate(-1)  # actor goes behind the circle; next label is removed
        removed.append(circle.popleft())
    return removed, circle[0]
