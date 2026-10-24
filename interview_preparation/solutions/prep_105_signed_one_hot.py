"""Test the complete two's-complement int32 bit pattern, including its sign bit."""
MASK32 = (1 << 32) - 1


def is_one_bit_active(n):
    if isinstance(n, bool) or not isinstance(n, int) or not -(1 << 31) <= n < (1 << 31):
        raise ValueError('n must be a signed 32-bit integer')
    u = n & MASK32
    return u != 0 and (u & (u - 1)) == 0
