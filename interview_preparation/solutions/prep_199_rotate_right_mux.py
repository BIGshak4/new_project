"""Combinational power-of-two-width barrel rotation, using only 2:1 MUXes."""


def mux(select, first, second):
    return second if select else first


def rotate_right(value, width=8, amount=0):
    if width < 1 or width & (width - 1):
        raise ValueError("width must be a positive power of two")
    if not 0 <= value < 1 << width or not 0 <= amount < width:
        raise ValueError("value and amount exceed their declared widths")
    bits = [(value >> i) & 1 for i in range(width)]
    for stage in range(width.bit_length() - 1):
        distance = 1 << stage
        bits = [mux((amount >> stage) & 1, bits[i], bits[(i + distance) % width])
                for i in range(width)]
    return sum(bit << i for i, bit in enumerate(bits))
