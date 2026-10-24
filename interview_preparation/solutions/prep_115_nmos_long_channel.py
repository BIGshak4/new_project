"""Educational DC equation model, not a process/BSIM or measured-device model.

Enhancement NMOS, source tied to body, VDS >= 0, constant mobility and VT.
All voltages are volts, beta = mu_n * Cox * W/L is A/V**2; ID is amperes.
The ideal core omits subthreshold conduction and channel-length modulation.
"""
from math import isfinite


def nmos_current(vgs, vds, beta, vth):
    """Return (region, ID) for the declared long-channel model."""
    values = (vgs, vds, beta, vth)
    if any(isinstance(value, bool) or not isfinite(value) for value in values):
        raise ValueError("finite real parameters required")
    if beta <= 0 or vth <= 0 or vds < 0:
        raise ValueError("require beta > 0, VT > 0, VDS >= 0")
    overdrive = vgs - vth
    if overdrive <= 0:
        return "cutoff", 0.0
    if vds < overdrive:
        return "triode", beta * (overdrive * vds - vds * vds / 2)
    return "saturation", beta * overdrive * overdrive / 2


def saturation_with_clm(vgs, vds, beta, vth, channel_lambda):
    """Optional local CLM approximation, continuous at VDS = VGS - VT.

    Uses 1 + lambda*(VDS - VDSsat), lambda in 1/V. Valid only in
    saturation; lambda is not a universal device constant or a fit here.
    """
    region, current = nmos_current(vgs, vds, beta, vth)
    if not isfinite(channel_lambda) or channel_lambda < 0:
        raise ValueError("lambda must be finite and nonnegative")
    if region != "saturation":
        raise ValueError("optional CLM extension requires saturation")
    return current * (1 + channel_lambda * (vds - (vgs - vth)))
