"""Explicit ideal models; no circuit topology or material constants are inferred.

SI units throughout. These equations are not SPICE, silicon or field-solver
validation. The capacitor-terminated line and concentric ground are declared
illustrations, not reconstructions of missing source diagrams.
"""
from math import exp, expm1, isfinite, log, pi, sqrt

Q = 1.602176634e-19
K = 1.380649e-23
EPSILON_0 = 8.8541878128e-12


def positive(*values):
    if any(isinstance(x, bool) or not isinstance(x, (int, float))
           or not isfinite(x) or x <= 0 for x in values):
        raise ValueError("positive finite model parameters required")


def capacitive_line_step(incident, z0, capacitance, elapsed):
    """Load arrival is t=0, zero initial capacitor voltage, matched source.

    Return load voltage, reflected voltage and load current. incident is the
    incoming voltage-step amplitude, not the generator's open-circuit voltage.
    """
    positive(z0, capacitance)
    if any(isinstance(x, bool) or not isinstance(x, (int, float))
           or not isfinite(x) for x in (incident, elapsed)) or elapsed < 0:
        raise ValueError("finite step amplitude and nonnegative elapsed time required")
    decay = exp(-elapsed / (z0 * capacitance))
    load = -2 * incident * expm1(-elapsed / (z0 * capacitance))
    reflected = load - incident
    current = 2 * incident * decay / z0
    return load, reflected, current


def capacitive_reflection(omega, z0, capacitance):
    """Frequency-domain coefficient; omega=0 uses its DC limiting value."""
    positive(z0, capacitance)
    if isinstance(omega, bool) or not isinstance(omega, (int, float)) \
            or not isfinite(omega) or omega < 0:
        raise ValueError("nonnegative finite angular frequency required")
    scaled = 1j * omega * z0 * capacitance
    return (1 - scaled) / (1 + scaled)


def outer_coax_capacitance_per_length(radius, ground_radius, permittivity):
    """Exterior field only: a conductor of outer radius R within ground b>R.

    Any fully enclosed charge-free cavity inside this conductor has zero field
    and does not change this exterior capacitance. End effects are excluded.
    """
    positive(radius, ground_radius, permittivity)
    if ground_radius <= radius:
        raise ValueError("ground radius must exceed conductor outer radius")
    return 2 * pi * permittivity / log(ground_radius / radius)


def abrupt_junction(acceptors, donors, intrinsic, permittivity, temperature,
                    applied_voltage=0.0):
    """Uniform abrupt nondegenerate PN junction, depletion approximation.

    Concentrations are m^-3; voltage is p-side minus n-side (positive forward).
    Width expression requires Vbi-Va>0 and excludes breakdown/high injection.
    """
    positive(acceptors, donors, intrinsic, permittivity, temperature)
    if isinstance(applied_voltage, bool) or not isinstance(applied_voltage, (int, float)) \
            or not isfinite(applied_voltage):
        raise ValueError("finite applied voltage required")
    thermal = K * temperature / Q
    built_in = thermal * (log(acceptors / intrinsic) + log(donors / intrinsic))
    barrier = built_in - applied_voltage
    if barrier <= 0:
        raise ValueError("depletion model requires a positive remaining barrier")
    width = sqrt(2 * permittivity * barrier / Q * (1 / acceptors + 1 / donors))
    p_width = width * donors / (acceptors + donors)
    n_width = width * acceptors / (acceptors + donors)
    field_peak = Q * donors * n_width / permittivity
    return {'thermal_voltage': thermal, 'built_in_voltage': built_in, 'width': width,
            'p_width': p_width, 'n_width': n_width, 'field_peak': field_peak,
            'capacitance_per_area': permittivity / width}
