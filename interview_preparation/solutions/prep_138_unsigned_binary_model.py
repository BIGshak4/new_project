"""Executable Python equivalent of the accompanying, uncompiled C algorithm.

width bounds the unsigned input in this model; C uses its unsigned int type.
The model's validation is not an extra validation promise made by C.
"""


def unsigned_to_binary(value, out, capacity, *, width=32):
    if type(width) is not int or width < 1:
        raise ValueError("positive unsigned width required")
    if type(value) is not int or not 0 <= value < (1 << width):
        raise ValueError("value must fit the unsigned word")
    if type(capacity) is not int or capacity < 0:
        raise ValueError("nonnegative capacity required")
    if out is not None and capacity > len(out):
        raise ValueError("capacity exceeds actual writable storage")
    probe, digits = value, 1
    probe >>= 1
    while probe != 0:
        digits += 1
        probe >>= 1
    if out is None or capacity <= digits:
        return False
    out[digits] = 0
    i = digits
    while i:
        i -= 1
        out[i] = ord("0") + (value & 1)
        value >>= 1
    return True
