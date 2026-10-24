"""Zero-only XOR network and explicit register-to-register timing arithmetic.

Nanoseconds are exact Fractions; this is a teaching model, not timing analysis
of a characterized cell library or an HDL simulation.
"""

from fractions import Fraction


def bit(value):
    if type(value) is not int or value not in (0, 1):
        raise ValueError("binary integer required")
    return value


def mux(select, d0, d1):
    select, d0, d1 = bit(select), bit(d0), bit(d1)
    return (1 - select) * d0 + select * d1


def xor_zero_only(a, b):
    """Original PREP-031 wiring, unchanged: inner (b,a,0), outer (a,b,t)."""
    a, b = bit(a), bit(b)
    intermediate = mux(b, a, 0)
    return mux(a, b, intermediate)


def required_period_ns(combinational, *, clock_to_q=0, setup=0, skew=0, uncertainty=0):
    """skew=capture_clock_arrival-launch_clock_arrival; setup margin included."""
    values = [Fraction(x) for x in (combinational, clock_to_q, setup, uncertainty)]
    if values[0] <= 0 or any(value < 0 for value in values[1:]):
        raise ValueError("positive path delay and nonnegative overheads required")
    period = sum(values) - Fraction(skew)
    if period <= 0:
        raise ValueError("model gives no positive period; other constraints are required")
    return period


def maximum_frequency_hz(combinational, **overheads):
    return Fraction(10**9, 1) / required_period_ns(combinational, **overheads)


def hold_is_met(contamination, *, clock_to_q_min=0, hold=0, skew=0):
    """This separate minimum-delay test does not depend on the clock period."""
    values = [Fraction(x) for x in (contamination, clock_to_q_min, hold)]
    if any(value < 0 for value in values):
        raise ValueError("minimum delays and hold must be nonnegative")
    return values[0] + values[1] >= Fraction(skew) + values[2]
