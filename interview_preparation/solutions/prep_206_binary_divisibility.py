"""Divisibility of a nonnegative binary integer by powers of two."""


def divisible_by_power_of_two(number: int, exponent: int) -> bool:
    if type(number) is not int or type(exponent) is not int or number < 0 or exponent < 0:
        raise ValueError("Require a nonnegative integer number and exponent")
    mask = (1 << exponent) - 1
    return (number & mask) == 0


def divisibility_2_4_8(number: int) -> tuple[bool, bool, bool]:
    if type(number) is not int or number < 0:
        raise ValueError("Require a nonnegative integer")
    return (number & 1) == 0, (number & 3) == 0, (number & 7) == 0
