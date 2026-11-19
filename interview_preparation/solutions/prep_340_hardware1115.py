"""Parallel presence equations; no pairwise arithmetic comparison."""


def maximum16(words):
    if len(words) != 16 or any(type(x) is not int or not 0 <= x <= 3 for x in words):
        raise ValueError("sixteen unsigned two-bit words required")
    high = low = three = 0
    for word in words:
        h, l = (word >> 1) & 1, word & 1
        high |= h
        low |= l
        three |= h & l
    return (high << 1) | (three | ((1-high) & low))
