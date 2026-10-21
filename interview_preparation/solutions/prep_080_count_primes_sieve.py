"""Count primes in the inclusive interval [1,n] with Eratosthenes' sieve."""

from math import isqrt


def count_primes(n: int) -> int:
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if n < 2:
        return 0
    prime = bytearray(b"\x01") * (n + 1)
    prime[0] = prime[1] = 0
    for p in range(2, isqrt(n) + 1):
        if prime[p]:
            for multiple in range(p * p, n + 1, p):
                prime[multiple] = 0
    return sum(prime)
