"""DC linear feedback model; not a saturation or transistor-level model."""
from fractions import Fraction as F


def closed_loop_gain(ground_r, feedback_r, open_loop=None):
    ground_r, feedback_r = F(ground_r), F(feedback_r)
    if ground_r <= 0 or feedback_r <= 0:
        raise ValueError("Positive resistances required")
    beta = ground_r/(ground_r+feedback_r)
    if open_loop is None:
        return 1/beta
    open_loop = F(open_loop)
    if open_loop <= 0:
        raise ValueError("Positive real DC open-loop gain required")
    return open_loop/(1+open_loop*beta)
