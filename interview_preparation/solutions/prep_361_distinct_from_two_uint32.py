"""Bit witnesses make an unsigned result different from both unsigned inputs.

Precondition: exact integers 0 <= a,b < 2**32. No validation branch is part
of this branch-free reference. Python's AND masks restrict output to 0..3.
"""


def different_uint32(a, b):
    return ((~a) & 1) | ((~b) & 2)
