"""Ideal unclamped RC step model, not a transistor or hardware simulation."""

from math import exp, log


def settle(c_start, duration, tau=1.0, vdd=1.0):
    if tau <= 0 or duration < 0 or vdd <= 0:
        raise ValueError("Positive time constant/supply and nonnegative duration required")
    return vdd + (c_start - vdd) * exp(-duration / tau)


def capacitor_step(c_before, b_before, b_after):
    """The voltage C-B across an ideal series capacitor is continuous."""
    return c_before + b_after - b_before


def inverter(voltage, vdd=1.0, threshold=0.5):
    """Ideal zero-delay decision, including an explicit equality convention."""
    return vdd if voltage < threshold else 0.0


def pulse_end(c_start, tau=1.0, vdd=1.0, threshold=0.5):
    if tau <= 0 or not 0 < threshold < vdd:
        raise ValueError("Threshold must lie strictly inside the supply rails")
    if c_start >= threshold:
        return 0.0
    return tau * log((vdd - c_start) / (vdd - threshold))


def trace(edges, times, *, tau=1.0, vdd=1.0):
    """A starts LOW, B=C=VDD after long settling; edges are (time,new_A_bit).

    Recompute each sample from events; O(events*samples), used for explanation.
    Right-continuous samples apply an edge before returning its new voltages.
    """
    if any(t < 0 for t in times):
        raise ValueError("Sample times must be nonnegative")
    if any(t < 0 or bit not in (0, 1) for t, bit in edges):
        raise ValueError("Invalid input edge")
    if any(edges[i][0] >= edges[i + 1][0] for i in range(len(edges) - 1)):
        raise ValueError("Input edges must have strictly increasing times")
    result = []
    for time in times:
        a, b, c, previous = 0.0, vdd, vdd, 0.0
        for edge_time, bit in edges:
            if edge_time > time:
                break
            c = settle(c, edge_time - previous, tau, vdd)
            next_b = vdd * (1 - bit)
            c = capacitor_step(c, b, next_b)
            a, b, previous = vdd * bit, next_b, edge_time
        c = settle(c, time - previous, tau, vdd)
        result.append((a, b, c, inverter(c, vdd, vdd / 2)))
    return result
