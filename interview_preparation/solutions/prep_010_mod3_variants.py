"""Synchronous modulo-three counters. State is (q1,q0), q1 most significant."""

def dff_next(q1, q0):
    return q0, (1-q1) & (1-q0)


def tff_inputs(q1, q0):
    return q1 | q0, 1-q1


def tff_next(q1, q0):
    t1, t0 = tff_inputs(q1, q0)
    return q1 ^ t1, q0 ^ t0


def adder_next(q1, q0):
    count = (q1 << 1) | q0
    incremented = (count + 1) & 3
    next_count = 0 if q1 else incremented
    return next_count >> 1, next_count & 1
