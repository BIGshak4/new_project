"""Finite one-shot stream; promised distinct range values and omission count.

One/two STREAMING NUMERIC ACCUMULATORS. The current item, n, loop control and
post-stream arithmetic scratch/output are allowed. No full validity check or
input materialization is hidden in the accumulator budget.
"""
from math import isqrt


def missing_one_once(values, n=100):
    if type(n) is not int or n < 1:
        raise ValueError("n must be a positive integer")
    difference = n * (n + 1) // 2
    for value in values:
        difference -= value
    return difference


def missing_two_once(values, n=100):
    if type(n) is not int or n < 2:
        raise ValueError("two omissions require n at least two")
    sum_difference = n * (n + 1) // 2
    square_difference = n * (n + 1) * (2 * n + 1) // 6
    for value in values:
        sum_difference -= value
        square_difference -= value * value
    discriminant = 2 * square_difference - sum_difference * sum_difference
    if discriminant <= 0:
        raise ValueError("not two distinct omissions under the promise")
    root = isqrt(discriminant)
    if root * root != discriminant or (sum_difference - root) % 2:
        raise ValueError("nonintegral omission candidates")
    first, second = (sum_difference - root) // 2, (sum_difference + root) // 2
    if not 1 <= first < second <= n:
        raise ValueError("candidate values outside the promised domain")
    return first, second
