"""Ideal retained binary nodes, not a transistor/charge simulation."""


def settle(a, b, n, y):
    if any(bit not in (0, 1) for bit in (a, b, n, y)):
        raise ValueError("binary model requires known initial node values")
    if not a:
        n = b
    elif b ^ y:
        y = n
    enable = a & (b ^ y)
    return n, y, enable
