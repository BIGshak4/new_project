"""Gate equations for the exact square of an unsigned two-bit input."""


def square(value):
    if type(value) is not int or not 0 <= value < 4:
        raise ValueError("unsigned two-bit input required")
    a, b = (value >> 1) & 1, value & 1
    y3, y2, y1, y0 = a & b, a & (b ^ 1), 0, b
    return (y3 << 3) | (y2 << 2) | (y1 << 1) | y0
