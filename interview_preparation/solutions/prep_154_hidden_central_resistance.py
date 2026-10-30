"""Recover the central tree resistance from four accessible-terminal readings."""


def infer_central_resistance(measure):
    """``measure(a,b)`` is an ohmmeter with all other terminals floating.

    Terminals 0,1,2 are the left leaves and 3,4,5 are the right leaves.
    The caller owns the power-off, linear resistor and no-external-load contract.
    """
    cross_first = measure(0, 3)
    cross_second = measure(1, 4)
    left_pair = measure(0, 1)
    right_pair = measure(3, 4)
    return (cross_first + cross_second - left_pair - right_pair) / 2
