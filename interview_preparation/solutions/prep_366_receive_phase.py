"""Two calibrated receive channels in a single-source plane wave."""

from math import acos, cos, isfinite, pi, remainder, tau


def projected_path(spacing: float, angle: float) -> float:
    """Return signed r2-r1 for angle from the antenna 2 to antenna 1 baseline."""
    if not isfinite(spacing) or spacing < 0:
        raise ValueError('spacing must be finite and nonnegative')
    if not 0 <= angle <= pi:
        raise ValueError('angle must be in [0, pi]')
    return spacing * cos(angle)


def wrap_phase(phase: float) -> float:
    """Use the half-open principal range [-pi, pi)."""
    if not isfinite(phase):
        raise ValueError('phase must be finite')
    principal = remainder(phase, tau)
    return -pi if principal == pi else principal


def observed_phase(spacing: float, angle: float, wavelength: float) -> float:
    """Phase at antenna 1 minus phase at antenna 2, with e^(jωt)."""
    if not isfinite(wavelength) or wavelength <= 0:
        raise ValueError('wavelength must be finite and positive')
    return wrap_phase(tau * (projected_path(spacing, angle) / wavelength))


def recover_angle(spacing: float, phase: float, wavelength: float) -> float:
    """Invert an ideal phase measurement with 0 < spacing < wavelength/2."""
    if not isfinite(wavelength) or not 0 < spacing < wavelength / 2:
        raise ValueError('unique recovery on the closed half-plane needs 0 < d < λ/2')
    scale = tau * (spacing / wavelength)
    if scale == 0:
        raise ValueError('spacing-to-wavelength ratio below floating-point resolution')
    cosine = wrap_phase(phase) / scale
    # Allow floating-point roundoff at the two endpoints of the ideal phase range.
    if abs(cosine) > 1.0 + 1e-12:
        raise ValueError('phase outside the model range')
    return acos(max(-1.0, min(1.0, cosine)))
