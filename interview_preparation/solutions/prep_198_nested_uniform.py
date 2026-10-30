"""Exact discrete marginals for inclusive A~Uniform{0..M}, B|A~Uniform{0..A}."""

from fractions import Fraction


def nested_marginals(upper=100):
    if not isinstance(upper, int) or upper < 0:
        raise ValueError("Inclusive upper bound must be a nonnegative integer")
    a_mass = [Fraction(1, upper + 1)] * (upper + 1)
    b_mass = [Fraction()] * (upper + 1)
    suffix = Fraction()
    for value in range(upper, -1, -1):
        suffix += Fraction(1, (upper + 1) * (value + 1))
        b_mass[value] = suffix
    return a_mass, b_mass


def joint_probability(a, b, upper=100):
    if not isinstance(upper, int) or upper < 0:
        raise ValueError("Invalid inclusive upper bound")
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("A and B must be integers")
    return Fraction(1, (upper + 1) * (a + 1)) if 0 <= b <= a <= upper else Fraction()
