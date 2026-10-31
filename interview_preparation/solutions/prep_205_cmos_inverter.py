"""Ideal rail-input switch model, separate from any analog transfer curve."""


def rail_inverter(vin_bit):
    if vin_bit not in (0, 1):
        raise ValueError("rail model accepts only zero or one")
    pmos_on = vin_bit == 0
    nmos_on = vin_bit == 1
    return {"pmos_on": pmos_on, "nmos_on": nmos_on,
            "vout_bit": 1 - vin_bit, "ideal_dc_rail_path": pmos_on and nmos_on}


def gate_overdrive_flags(vin, vdd=1.0, vtn=0.3, vtp_abs=0.3):
    if not 0 <= vin <= vdd or min(vtn, vtp_abs) <= 0:
        raise ValueError("positive thresholds and legal input voltage required")
    # Only indicates possible channel conduction, not output voltage/current.
    return vin > vtn, (vdd - vin) > vtp_abs
