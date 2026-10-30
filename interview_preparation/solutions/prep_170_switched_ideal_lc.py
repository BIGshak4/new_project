"""Isolated ideal LC after disconnecting the charging source; passive iL downward."""

from math import cos, isfinite, sin, sqrt


def response(time, inductance, capacitance, initial_voltage):
    if not all(isfinite(v) for v in (time, inductance, capacitance, initial_voltage)):
        raise ValueError("finite parameters required")
    if time < 0 or inductance <= 0 or capacitance <= 0:
        raise ValueError("nonnegative time and positive L,C required")
    omega = 1 / sqrt(inductance * capacitance)
    voltage = initial_voltage * cos(omega * time)
    current_l = initial_voltage * sqrt(capacitance / inductance) * sin(omega * time)
    return voltage, current_l
