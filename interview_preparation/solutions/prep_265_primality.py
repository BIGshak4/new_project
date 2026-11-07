"""Exact predicate for a single nonnegative integer; word cost is width-dependent."""


def is_prime(n):
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    divisor = 3
    while divisor <= n // divisor:
        if n % divisor == 0:
            return False
        divisor += 2
    return True
