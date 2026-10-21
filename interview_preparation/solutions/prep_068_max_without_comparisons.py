"""Exact-integer and fixed-width models; no ordering comparisons in either.

The first method permits abs. The second assumes a and b are valid signed
32-bit integers and models uint32_t arithmetic explicitly.
"""


def max_without_comparisons(a, b):
    return (a + b + abs(a - b)) // 2


def max_i32_model(a, b):
    word_mask = (1 << 32) - 1
    ua, ub = a & word_mask, b & word_mask
    sa, sb = ua >> 31, ub >> 31
    different = sa ^ sb
    difference_sign = ((ua - ub) & word_mask) >> 31
    choose_b = (different & sa) | ((different ^ 1) & difference_sign)
    mask = (-choose_b) & word_mask
    bits = (ua & (word_mask ^ mask)) | (ub & mask)
    return (bits & ((1 << 31) - 1)) - (bits >> 31) * (1 << 31)
