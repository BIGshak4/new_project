"""Explicit added resistor-switch example, not the ambiguous source's circuit."""

from math import exp


def drain_after_gate_turn_on(time, *, supply=3.3, pullup=1000.0, on_resistance=100.0, load_capacitance=1e-9):
    """Gate is an externally forced step; output starts at supply and relaxes.

    Model NMOS as Ron after turn-on. Rpullup remains attached. No gate slew,
    threshold transition, channel-charge effect or physical device fit is implied.
    """
    if min(supply, pullup, on_resistance, load_capacitance) <= 0 or time < 0:
        raise ValueError("positive parameters and nonnegative time required")
    final_voltage = supply * on_resistance / (pullup + on_resistance)
    equivalent = pullup * on_resistance / (pullup + on_resistance)
    tau = equivalent * load_capacitance
    return final_voltage + (supply - final_voltage) * exp(-time / tau)
