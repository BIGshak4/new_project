"""Settled clock-edge model for continuous serial pattern 01011.

One MSB-temporal-order bit is accepted per rising edge. Reset overrides it.
State k means the longest pattern prefix that is a suffix of received history;
Moore state 5 asserts the detection output for the following cycle.
No HDL compilation or physical timing is represented.
"""

MOORE_NEXT = ((1, 0), (1, 2), (3, 0), (1, 4), (3, 5), (1, 0))
MEALY_NEXT = ((1, 0), (1, 2), (3, 0), (1, 4), (3, 0))


def moore_step(state, bit, reset=0):
    if type(state) is not int or state not in range(6):
        raise ValueError("Moore state must be 0..5")
    if any(type(x) is not int or x not in (0, 1) for x in (bit, reset)):
        raise ValueError("binary integer data/reset required")
    return 0 if reset else MOORE_NEXT[state][bit]


def moore_output(state):
    if type(state) is not int or state not in range(6):
        raise ValueError("Moore state must be 0..5")
    return int(state == 5)


def mealy_event(state, bit):
    if type(state) is not int or state not in range(5):
        raise ValueError("Mealy prefix state must be 0..4")
    if type(bit) is not int or bit not in (0, 1):
        raise ValueError("binary integer data required")
    return MEALY_NEXT[state][bit], int(state == 4 and bit == 1)
