"""Ideal concentric-circle rope clearance, in metres; no physical sag model."""
from math import isfinite, pi


def uniform_clearance(extra_length=10.0):
    """Return the uniform radial gap for a nonnegative extra circumference."""
    value = float(extra_length)
    if not isfinite(value) or value < 0:
        raise ValueError("extra_length must be finite and nonnegative")
    return value / (2 * pi)


def extra_length_for_clearance(height):
    """Required added circumference for a nonnegative uniform radial gap."""
    value = float(height)
    if not isfinite(value) or value < 0:
        raise ValueError("height must be finite and nonnegative")
    return 2 * pi * value
