"""Lumped capacitive illustration with prescribed aligned ramp slopes."""

from math import isfinite, log


def effective_capacitance(ground_c, coupling_c, aggressor_slope_ratio):
    values = (ground_c, coupling_c, aggressor_slope_ratio)
    if not all(isfinite(value) for value in values):
        raise ValueError("finite parameters required")
    if ground_c <= 0 or coupling_c < 0 or aggressor_slope_ratio not in (-1, 0, 1):
        raise ValueError("Cg>0, Cc>=0 and aligned ratio -1,0,1 required")
    return ground_c + coupling_c * (1 - aggressor_slope_ratio)


def illustrative_delay(resistance, ground_c, coupling_c, aggressor_slope_ratio):
    if not isfinite(resistance) or resistance <= 0:
        raise ValueError("positive finite resistance required")
    return log(2) * resistance * effective_capacitance(ground_c, coupling_c, aggressor_slope_ratio)
