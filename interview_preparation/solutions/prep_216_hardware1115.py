"""Source-edge phase model of three taps and common-low selection."""


def rising(count):
    if type(count) is not int or not 0 <= count < 8:
        raise ValueError("three-bit counter state required")
    q0, q1, q2 = count & 1, (count >> 1) & 1, (count >> 2) & 1
    return ((q2 ^ (q1 & q0)) << 2) | ((q1 ^ q0) << 1) | (1-q0)


def falling(count, active, requested):
    if active not in (0, 1, 2) or requested not in (0, 1, 2):
        raise ValueError("tap code must be zero, one or two")
    return requested if count == 0 else active


def output(count, active):
    return (count >> active) & 1
