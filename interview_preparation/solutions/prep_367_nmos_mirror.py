"""Ideal long-channel NMOS current mirror, with fixed output drain voltage."""

from math import isfinite, sqrt


def output_current(reference_current: float, output_voltage: float,
                   beta_reference: float = 1.0, beta_output: float = 2.0) -> float:
    """Give the sink current in mA for voltage in V and beta in mA/V²."""
    if not all(isfinite(value) for value in (reference_current, output_voltage, beta_reference, beta_output)):
        raise ValueError('model parameters must be finite')
    if reference_current < 0 or output_voltage < 0 or beta_reference <= 0 or beta_output <= 0:
        raise ValueError('currents and voltages must be nonnegative and beta values positive')
    overdrive = sqrt(2.0 * reference_current / beta_reference)
    if output_voltage >= overdrive:
        return reference_current * beta_output / beta_reference
    return beta_output * output_voltage * (overdrive - output_voltage / 2.0)


def reference_current_at_knee(output_voltage: float, beta_reference: float = 1.0) -> float:
    """Current in mA where the output device reaches the saturation boundary."""
    if (not isfinite(output_voltage) or not isfinite(beta_reference)
            or output_voltage < 0 or beta_reference <= 0):
        raise ValueError('output voltage must be nonnegative and beta positive, both finite')
    return beta_reference * output_voltage ** 2 / 2.0
