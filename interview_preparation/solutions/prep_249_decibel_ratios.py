"""Positive power ratios; voltage ratios use equal resistive impedances."""
import math


def power_db(output_power, input_power):
    if not all(math.isfinite(x) and x > 0 for x in (output_power, input_power)):
        raise ValueError('Finite positive powers required')
    return 10 * (math.log10(output_power) - math.log10(input_power))


def voltage_db_equal_impedance(output_rms, input_rms):
    if not all(math.isfinite(x) and x > 0 for x in (output_rms, input_rms)):
        raise ValueError('Finite positive RMS magnitudes required')
    return 20 * (math.log10(output_rms) - math.log10(input_rms))


def watts_to_dbm(watts):
    return power_db(watts, 0.001)
