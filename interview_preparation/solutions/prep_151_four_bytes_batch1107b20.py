"""Use the supplied byte-count operation exactly four times; uint32 input."""


def count_uint32(value, byte_count):
    if type(value) is not int or not 0 <= value < (1 << 32):
        raise ValueError('value must be an unsigned 32-bit integer')
    return (byte_count(value & 0xff)
            + byte_count((value >> 8) & 0xff)
            + byte_count((value >> 16) & 0xff)
            + byte_count((value >> 24) & 0xff))
