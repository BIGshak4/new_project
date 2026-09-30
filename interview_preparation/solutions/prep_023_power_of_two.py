"""Input contract: n is an integer; 1=2**0 is included."""


def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0
