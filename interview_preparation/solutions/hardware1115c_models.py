"""Finite occupancy controller and explicit first-order inverter delay model."""
from math import isfinite, sqrt


def parking_step(occupancy, entry, exit_event, reset=False):
    if type(occupancy) is not int or not 0 <= occupancy < 64:
        raise ValueError("six-bit state required")
    if any(type(v) is not bool for v in (entry, exit_event, reset)):
        raise ValueError("Boolean events required")
    state_error = occupancy > 50
    exit_ok = not reset and not state_error and exit_event and occupancy > 0
    entry_ok = not reset and not state_error and entry and (occupancy < 50 or exit_ok)
    result = 0 if reset or state_error else occupancy + entry_ok - exit_ok
    return result, entry_ok, exit_ok


def delay(scale, first_load, middle_drive, fixed):
    values = scale, first_load, middle_drive, fixed
    if not all(isfinite(v) for v in values):
        raise ValueError("finite parameters required")
    if min(scale, first_load, middle_drive) <= 0 or fixed < 0:
        raise ValueError("positive scale/A/B and nonnegative C required")
    return first_load*scale + middle_drive/scale + fixed


def optimum(first_load, middle_drive):
    if not all(isfinite(v) and v > 0 for v in (first_load, middle_drive)):
        raise ValueError("positive finite A and B required")
    return sqrt(middle_drive/first_load)
