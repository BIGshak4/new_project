"""Four-input OR from two copies of a 2-of-4 threshold box and constants."""


def box(a, b, c, d):
    return int(a + b + c + d >= 2)


def proposed(a, b, c, d):
    intermediate = box(a, b, c, 1)
    return box(intermediate, d, 1, 0)
