"""First-order capacitive-load illustration, not a characterized transistor model."""
from math import exp, isfinite, log


def falling_output(time, delay=0.2, tau=0.5, vdd=1.0):
    if (not all(isfinite(v) for v in (time, delay, tau, vdd))
            or delay < 0 or tau <= 0 or vdd <= 0):
        raise ValueError("finite time and positive physical constants required")
    return vdd if time <= delay else vdd * exp(-(time - delay) / tau)


def threshold_crossing(fraction, delay=0.2, tau=0.5):
    if not 0 < fraction < 1 or delay < 0 or tau <= 0:
        raise ValueError("fraction in (0,1) and legal timing constants required")
    return delay - tau * log(fraction)
