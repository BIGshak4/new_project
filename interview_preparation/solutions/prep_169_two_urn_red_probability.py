"""Uniform urn then uniform ball; all fifty red/fifty white balls allocated."""

from fractions import Fraction


def red_probability(red_first, white_first):
    if any(type(x) is not int or not 0 <= x <= 50 for x in (red_first, white_first)):
        raise ValueError("each allocation count must lie in0..50")
    first = red_first + white_first
    second = 100 - first
    if first == 0 or second == 0:
        raise ValueError("both urns must be nonempty")
    return (Fraction(red_first, first) + Fraction(50 - red_first, second)) / 2


def best_allocations():
    optimum, choices = Fraction(-1), []
    for red in range(51):
        for white in range(51):
            if red + white in (0, 100):
                continue
            value = red_probability(red, white)
            if value > optimum:
                optimum, choices = value, [(red, white)]
            elif value == optimum:
                choices.append((red, white))
    return optimum, tuple(choices)
