"""Ideal first-order RC inference, not an instrument driver or physical experiment."""

from math import expm1, inf, isfinite


def _positive(value: float, name: str) -> float:
    value = float(value)
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def effective_resistance(resistor_ohm: float, source_ohm: float = 0,
                         probe_ohm: float = inf) -> float:
    """Resistance seen by C after the ideal voltage source is set to zero.

    External resistor plus source resistance, in parallel with a finite probe
    input resistance. Leakage, when known, may be combined into probe_ohm.
    """
    resistor = _positive(resistor_ohm, "resistor_ohm")
    source = float(source_ohm)
    probe = float(probe_ohm)
    if not isfinite(source) or source < 0:
        raise ValueError("source_ohm must be finite and nonnegative")
    series = resistor + source
    if not isfinite(series):
        raise ValueError("series resistance exceeds the model's finite range")
    if probe == inf:
        return series
    probe = _positive(probe, "probe_ohm")
    return 1 / (1 / series + 1 / probe)


def infer_capacitance(resistor_ohm: float, tau_seconds: float, *,
                      source_ohm: float = 0, probe_ohm: float = inf,
                      probe_farad: float = 0) -> float:
    """Use the measured 1-e^-1 transition time, correcting the declared RC load."""
    tau = _positive(tau_seconds, "tau_seconds")
    parasitic = float(probe_farad)
    if not isfinite(parasitic) or parasitic < 0:
        raise ValueError("probe_farad must be finite and nonnegative")
    resistance = effective_resistance(resistor_ohm, source_ohm, probe_ohm)
    inferred = tau / resistance - parasitic
    if not isfinite(inferred) or inferred <= 0:
        raise ValueError("measurements do not imply a positive finite DUT capacitance")
    return inferred


def transition_voltage(time_seconds: float, tau_seconds: float,
                       initial_volt: float = 0, final_volt: float = 1) -> float:
    """First-order transition: v0+(vinf-v0)*(1-exp(-t/tau))."""
    time = float(time_seconds)
    tau = _positive(tau_seconds, "tau_seconds")
    initial, final = float(initial_volt), float(final_volt)
    if not isfinite(time) or time < 0 or not all(map(isfinite, (initial, final))):
        raise ValueError("time must be nonnegative; time and levels must be finite")
    return initial + (final - initial) * -expm1(-time / tau)
