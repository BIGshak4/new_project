"""General unsigned32 population count; byte-specific part is kept separately."""


def popcount(x):
    if not 0 <= x < (1 << 32):
        raise ValueError('Unsigned 32-bit input required')
    count = 0
    while x:
        x &= x - 1
        count += 1
    return count
