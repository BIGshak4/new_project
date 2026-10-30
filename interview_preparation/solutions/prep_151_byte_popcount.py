"""Byte popcount: fixed scan, sparse scan, parallel groups and a lookup table.

Every method is O(1) when the entire domain is a fixed byte. The parallel
formula has no per-bit loop; the table has an explicit one-time construction.
"""


def valid_byte(value):
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError("an unsigned byte in 0..255 is required")


def count_scan(value):
    valid_byte(value)
    result = 0
    for _ in range(8):
        result += value & 1
        value >>= 1
    return result


def count_sparse(value):
    valid_byte(value)
    result = 0
    while value:
        value &= value - 1
        result += 1
    return result


def count_parallel(value):
    valid_byte(value)
    value = value - ((value >> 1) & 0x55)
    value = (value & 0x33) + ((value >> 2) & 0x33)
    return (value + (value >> 4)) & 0x0F


def build_table():
    table = [0] * 256
    for value in range(1, 256):
        table[value] = table[value >> 1] + (value & 1)
    return tuple(table)


BYTE_COUNTS = build_table()


def count_lookup(value):
    valid_byte(value)
    return BYTE_COUNTS[value]
