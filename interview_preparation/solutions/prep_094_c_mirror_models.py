"""Executable Python models of the two uncompiled C byte-reversal functions."""


def _byte(value):
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError("expect an integer in 0..255")


def reverse_loop(value):
    _byte(value)
    result = 0
    for _ in range(8):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result


def reverse_masks(value):
    _byte(value)
    value = ((value & 0x55) << 1) | ((value >> 1) & 0x55)
    value = ((value & 0x33) << 2) | ((value >> 2) & 0x33)
    return ((value & 0x0F) << 4) | ((value >> 4) & 0x0F)
