"""Educational long-channel DC model, not SPICE or a process-qualified design."""

from math import sqrt


def nmos_current(vgs, vds, beta, threshold):
    """Positive drain current for vds>=0; ignores leakage and channel modulation."""
    if beta <= 0 or vds < 0:
        raise ValueError("positive beta and nonnegative vds required")
    overdrive = vgs - threshold
    if overdrive <= 0:
        return 0.0
    if vds >= overdrive:
        return beta * overdrive * overdrive / 2
    return beta * (overdrive * vds - vds * vds / 2)


def threshold_with_body(output, threshold0, gamma=0.0, phi=0.6):
    if output < 0 or gamma < 0 or phi <= 0:
        raise ValueError("invalid body-effect parameters")
    return threshold0 + gamma * (sqrt(phi + output) - sqrt(phi))


def currents(
    vin,
    output,
    *,
    vdd=5.0,
    beta_driver=8.0,
    beta_load=1.0,
    driver_threshold=1.0,
    load_threshold=1.0,
    gamma=0.0,
    load_kind="enhancement",
):
    if not (0 <= vin <= vdd and 0 <= output <= vdd and vdd > 0):
        raise ValueError("voltages must lie between the rails")
    if load_kind == "enhancement":
        # Load drain and gate at VDD, source at output, body at ground.
        vt = threshold_with_body(output, load_threshold, gamma)
        iload = nmos_current(vdd - output, vdd - output, beta_load, vt)
    elif load_kind == "depletion":
        # Separate process/bias contract: negative threshold maintained, VGS=0.
        if load_threshold >= 0 or gamma != 0:
            raise ValueError("depletion illustration needs negative Vt and no body shift")
        iload = nmos_current(0.0, vdd - output, beta_load, load_threshold)
    else:
        raise ValueError("unknown load kind")
    idriver = nmos_current(vin, output, beta_driver, driver_threshold)
    return iload, idriver


def dc_output(vin, **parameters):
    """First current-balance boundary approached when output charges from below.

    In the ideal leakage-free enhancement-load model an OFF driver admits a
    continuum of charged floating equilibria above the load cutoff. Selecting
    the charging boundary is explicit, not a claim of a unique physical DC state.
    """
    vdd = parameters.get("vdd", 5.0)
    low, high = 0.0, vdd
    for _ in range(90):
        midpoint = (low + high) / 2
        iload, idriver = currents(vin, midpoint, **parameters)
        if iload > idriver:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2
