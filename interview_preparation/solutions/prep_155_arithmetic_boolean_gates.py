"""Arithmetic gates on scalar exact bits, not bitwise operations on words."""


def gates(x, y):
    """Caller guarantees x,y are 0 or 1; tuple is NOT(x),AND,OR,XOR."""
    return 1 - x, x * y, x + y - x * y, x + y - 2 * x * y
