"""Gate equations for unsigned eight-bit max(x,64), without state.

The primitive model is NOT/AND/OR plus wires; Python shifts and summation
only encode/decode bit vectors, not extra arithmetic hardware.
"""


def output_bits(x):
    """Accept/return eight bits in LSB-first list order."""
    if not isinstance(x, (tuple, list)) or len(x) != 8:
        raise ValueError("eight input bits required")
    if any(type(bit) is not int or bit not in (0, 1) for bit in x):
        raise ValueError("binary integer bits required")
    pass_low = x[7] | x[6]
    return tuple([x[index] & pass_low for index in range(6)] + [x[6] | (x[7] ^ 1), x[7]])


def clamp_lower64(value):
    if type(value) is not int or not 0 <= value < 256:
        raise ValueError("unsigned eight-bit input required")
    result = output_bits(tuple((value >> index) & 1 for index in range(8)))
    return sum(bit << index for index, bit in enumerate(result))
