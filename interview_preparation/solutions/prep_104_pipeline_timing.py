"""Ideal capture traces and scalar timing margins, not failure prediction.

An early or late observed transition alone cannot diagnose a timing violation.
skew means capture-clock arrival minus launch-clock arrival. Delays are supplied
in consistent units; maximum and minimum path values must describe one path.
"""


def pipeline(samples, *, initial=(0, 0, 0)):
    state = tuple(initial)
    if len(state) != 3 or any(type(x) is not int or x not in (0, 1) for x in state):
        raise ValueError("initial must contain three integer bits")
    states = []
    for value in samples:
        if type(value) is not int or value not in (0, 1):
            raise ValueError("samples must be integer bits")
        state = value, state[0], state[1]
        states.append(state)
    return states


def timing_slacks(*, period, cq_max, logic_max, setup,
                  cq_min, logic_min, hold, skew=0):
    nonnegative = (cq_max, logic_max, setup, cq_min, logic_min, hold)
    if period <= 0 or any(value < 0 for value in nonnegative):
        raise ValueError("positive period and nonnegative delays are required")
    if cq_min > cq_max or logic_min > logic_max:
        raise ValueError("minimum delay must not exceed maximum delay")
    return {
        "setup": period + skew - cq_max - logic_max - setup,
        "hold": cq_min + logic_min - skew - hold,
    }
