"""Synchronous-load modulo-eight box, reused without changing its internals."""


def load_decode(q):
    if type(q) is not int or not 0 <= q < 8:
        raise ValueError("q must be a three-bit unsigned value")
    a, b, c = (q >> 2) & 1, (q >> 1) & 1, q & 1
    return a & (b | c)


def step(q, initialize=False):
    load = load_decode(q) or initialize
    return 1 if load else (q + 1) & 7


def reduced_legal_cycle_decode(q):
    return ((q >> 2) & 1) & (q & 1)
