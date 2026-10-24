"""Settled voltage-decision models; not a physical comparator simulation.

Voltages use the same reference and units (volts). Device operating limits,
output loading, propagation delay and startup behavior require a datasheet.
None means that the declared model does not determine a digital result.
"""
from math import isfinite


def compare_voltage(vin, vref, uncertainty=0.0):
    """Non-inverting decision with a bounded differential uncertainty.

    At exact equality, or when the uncertainty interval includes zero,
    return None. This is not an assertion of a particular physical voltage.
    """
    if any(isinstance(x, bool) or not isfinite(x) for x in (vin, vref, uncertainty)):
        raise ValueError("finite voltages required")
    if uncertainty < 0:
        raise ValueError("uncertainty must be nonnegative")
    difference = vin - vref
    if abs(difference) <= uncertainty:
        return None
    return int(difference > 0)


def schmitt_step(vin, lower, upper, previous=None):
    """Ideal non-inverting hysteresis state, with lower < upper.

    Strict crossings set the state; the closed band retains previous.
    Retention at the exact boundaries is an explicit model convention,
    not a guarantee at the physical trip voltage. Unknown startup in the
    band remains None; a strict outer crossing determines it.
    """
    if any(isinstance(x, bool) or not isfinite(x) for x in (vin, lower, upper)):
        raise ValueError("finite voltages required")
    if lower >= upper or previous not in (None, 0, 1):
        raise ValueError("require lower < upper and previous in {None, 0, 1}")
    if vin > upper:
        return 1
    if vin < lower:
        return 0
    return previous
