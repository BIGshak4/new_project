"""Runtime expectations independent of the candidate references and inputs.

The prime oracle tries every divisor through exact isqrt, rather than the
candidate's odd-only loop with division-based stopping. The speed oracle uses
arithmetic clamping rather than the candidate lookup tables.
"""
from math import isqrt


def prime_oracle(n):
    return n >= 2 and all(n % divisor != 0 for divisor in range(2, isqrt(n) + 1))


def speed_oracle(speed):
    return [min(10, speed + 1), max(0, speed - 1)]


ORACLES = {
    "prep-primality-predicate-finite-input-domain": prime_oracle,
    "prep-branch-free-saturating-speed-controls": speed_oracle,
}
