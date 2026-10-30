"""Insert one of +,-,*,/ in each gap, ordinary precedence, exact fractions.

Digits stay in order; no concatenation, parentheses or unary signs needed.
The source does not specify an operator library; this is an explicit contract.
"""
from fractions import Fraction
from itertools import product

DIGITS = tuple(range(1, 10))
OPERATORS = ("+", "-", "*", "/")


def expression_value(operators, digits=DIGITS):
    if not digits or len(operators) != len(digits) - 1 or any(op not in OPERATORS for op in operators):
        raise ValueError("one allowed operator per gap is required")
    total, term, sign = Fraction(0), Fraction(digits[0]), 1
    for operator, value in zip(operators, digits[1:], strict=True):
        if operator in ("+", "-"):
            total += sign * term
            term, sign = Fraction(value), 1 if operator == "+" else -1
        elif operator == "*":
            term *= value
        else:
            term /= value
    return total + sign * term


def format_expression(operators):
    return "1" + "".join(operator + str(value) for operator, value in zip(operators, DIGITS[1:], strict=True))


def first_expression(target=100):
    for operators in product(OPERATORS, repeat=8):
        if expression_value(operators) == target:
            return format_expression(operators)
    return None
