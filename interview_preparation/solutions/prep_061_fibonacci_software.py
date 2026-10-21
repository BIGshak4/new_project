"""PREP-061: recursive Fibonacci, local memoization and iterative improvement.

Convention F(0)=0, F(1)=1; exact nonnegative integer indices, bool excluded.
Unit-cost arithmetic complexity differs from Python arbitrary-precision cost.
Recursive variants are for explanation/small n and depend on recursion limits.
"""
from functools import cache


def validate_index(n: int) -> None:
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer, not bool")


def fibonacci_recursive(n: int) -> int:
    validate_index(n)

    def fib(k: int) -> int:
        if k < 2:
            return k
        return fib(k - 1) + fib(k - 2)

    return fib(n)


def fibonacci_memoized(n: int) -> int:
    validate_index(n)

    @cache
    def fib(k: int) -> int:
        if k < 2:
            return k
        return fib(k - 1) + fib(k - 2)

    return fib(n)


def fibonacci_iterative(n: int) -> int:
    validate_index(n)
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
