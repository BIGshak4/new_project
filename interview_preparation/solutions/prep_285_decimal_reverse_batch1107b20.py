"""Signed int32 decimal reversal; 0 is also the overflow sentinel."""


def reverse_int32(n):
    if type(n) is not int or not -(1 << 31) <= n < (1 << 31):
        raise ValueError("n must be signed int32")
    negative = n < 0
    remaining = -n if negative else n  # Python magnitude is unbounded.
    limit = 1 << 31 if negative else (1 << 31) - 1
    result = 0
    while remaining:
        digit = remaining % 10
        remaining //= 10
        if result > (limit - digit) // 10:
            return 0
        result = result * 10 + digit
    return -result if negative else result
