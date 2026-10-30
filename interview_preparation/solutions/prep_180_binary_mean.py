"""Exact and floor arithmetic mean of two unsigned n-bit words."""


def mean_unsigned(a, b, width):
    if type(width) is not int or width < 1:
        raise ValueError("positive bit width required")
    if any(type(x) is not int or not 0 <= x < (1 << width) for x in (a, b)):
        raise ValueError("inputs must fit unsigned width")
    # Carry-out is retained: the addition conceptually has width+1 bits.
    total = a + b
    return total >> 1, total & 1  # integer part and a half-unit flag


def mean_without_wide_sum(a, b, width):
    mean_unsigned(a, b, width)  # validate the contract
    return (a & b) + ((a ^ b) >> 1), (a ^ b) & 1
