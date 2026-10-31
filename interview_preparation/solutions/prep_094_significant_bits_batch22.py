"""Reverse only significant bits of an unsigned 32-bit value; zero maps to zero."""


def reverse_significant(n):
    if type(n) is not int or not 0 <= n <= 0xffffffff:
        raise ValueError('unsigned 32-bit integer required')
    out = 0
    while n:
        out = (out << 1) | (n & 1)
        n >>= 1
    return out
