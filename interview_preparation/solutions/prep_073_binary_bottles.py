"""One-round binary pooling for the abstract 1000-bottle puzzle.

Public bottles are numbered 1..1000. Internal label = public number - 1.
Taster 1 encodes the least-significant bit; True means dead at the deadline.
"""

BOTTLES = 1000
TASTERS = 10


def tasting_groups():
    return [
        [bottle for bottle in range(1, BOTTLES + 1) if ((bottle - 1) >> taster) & 1]
        for taster in range(TASTERS)
    ]


def decode(dead):
    dead = tuple(dead)
    if len(dead) != TASTERS or any(type(value) is not bool for value in dead):
        raise ValueError("provide exactly ten Boolean end-of-day outcomes")
    label = sum((1 << bit) for bit, value in enumerate(dead) if value)
    if label >= BOTTLES:
        raise ValueError("unused outcome pattern: the declared model was violated")
    return label + 1


if __name__ == "__main__":
    groups = tasting_groups()
    poisoned = 14
    dead = tuple(poisoned in group for group in groups)
    print(decode(dead))
