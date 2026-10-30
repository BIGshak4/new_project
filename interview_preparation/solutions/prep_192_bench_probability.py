"""Exact probabilities for distinct people uniformly seated in a line."""

from fractions import Fraction


def right_of_probabilities(number_of_people):
    if not isinstance(number_of_people, int) or number_of_people < 2:
        raise ValueError("At least two distinct people are required")
    # Ordered adjacent block CF: (n-1)! of n! orders.
    immediate_right = Fraction(1, number_of_people)
    # Swapping C and F bijects right-of and left-of arrangements.
    anywhere_right = Fraction(1, 2)
    return immediate_right, anywhere_right
