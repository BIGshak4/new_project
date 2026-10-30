"""Reverse exactly the supplied width, retaining leading zero positions.

Scalar Python model. O(width) loop iterations; arbitrary-size bit-operation
costs depend on width. width=0 accepts only value=0 and returns zero.
"""


def reverse_bits(value, width):
    if type(width) is not int or width < 0:
        raise ValueError("width must be a nonnegative integer")
    if type(value) is not int or not 0 <= value < (1 << width):
        raise ValueError("value must fit the supplied unsigned width")
    result = 0
    for _ in range(width):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result
