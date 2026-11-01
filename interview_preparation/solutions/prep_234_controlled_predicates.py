"""Four independent Boolean predicates, selected by mode AB."""


def predicates(x):
    if type(x) is not int or not 0 <= x < 16:
        raise ValueError('unsigned four-bit input required')
    a, b, c, d = [(x >> bit) & 1 for bit in (3, 2, 1, 0)]
    any_zero = 1 - (a & b & c & d)
    majority = (a & b & c) | (a & b & d) | (a & c & d) | (b & c & d)
    odd = a ^ b ^ c ^ d
    return [any_zero, majority, odd, 1 - odd]


def controlled(x, mode):
    if type(mode) is not int or not 0 <= mode < 4:
        raise ValueError('two-bit mode required')
    return predicates(x)[mode]
