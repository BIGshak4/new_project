"""First-order illustrations only, not a transistor or transmission-line model."""

from math import isfinite, log


def rc_crossing(resistance, capacitance, fraction=0.5):
    if not all(isfinite(v) for v in (resistance, capacitance, fraction)):
        raise ValueError("finite parameters required")
    if resistance <= 0 or capacitance < 0 or not 0 < fraction < 1:
        raise ValueError("R>0, C>=0 and 0<fraction<1 required")
    return -resistance * capacitance * log(1 - fraction)


def compare_paths(source_r, load_c, buffer_input_c, buffer_r, intrinsic_delay):
    if not isfinite(intrinsic_delay) or intrinsic_delay < 0:
        raise ValueError("nonnegative finite intrinsic delay required")
    direct = rc_crossing(source_r, load_c)
    buffered = rc_crossing(source_r, buffer_input_c) + intrinsic_delay + rc_crossing(buffer_r, load_c)
    return direct, buffered
