"""Exact rejection sampling, assuming independent uniform random5 calls."""


def random7(random5):
    while True:
        first, second = random5(), random5()
        if type(first) is not int or type(second) is not int:
            raise ValueError("random5 must return integers")
        if not (0 <= first <= 4 and 0 <= second <= 4):
            raise ValueError("random5 must return values in 0..4")
        candidate = 5 * first + second
        if candidate < 21:
            return candidate % 7
