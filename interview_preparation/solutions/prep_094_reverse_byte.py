"""Reverse exactly eight bits using scalar bit operations, without an array."""


def reverse_byte(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
        raise ValueError("value must be an integer in 0..255")
    result = 0
    for _ in range(8):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result
