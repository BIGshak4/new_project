"""Unsigned 8-bit input -> zero or a one-hot mask for its highest set bit."""


def isolate_msb(x: int) -> int:
    if not 0 <= x <= 255:
        raise ValueError('Expected an unsigned eight-bit input')
    s1 = x | (x >> 1)
    s2 = s1 | (s1 >> 2)
    s3 = s2 | (s2 >> 4)
    return s3 ^ (s3 >> 1)


def priority_chain(x: int) -> int:
    if not 0 <= x <= 255:
        raise ValueError('Expected an unsigned eight-bit input')
    seen = 0
    output = 0
    for bit in range(7, -1, -1):
        current = (x >> bit) & 1
        output |= (current & (1-seen)) << bit
        seen |= current
    return output


def shared_prefix_xor(x: int) -> int:
    """7 two-input OR + 7 two-input XOR gates; wires are free in this model."""
    if not 0 <= x <= 255:
        raise ValueError('Expected an unsigned eight-bit input')
    p = [0] * 8
    p[7] = (x >> 7) & 1
    for i in range(6, -1, -1):
        p[i] = ((x >> i) & 1) | p[i+1]
    y = p[7] << 7
    for i in range(6, -1, -1):
        y |= (p[i] ^ p[i+1]) << i
    return y
