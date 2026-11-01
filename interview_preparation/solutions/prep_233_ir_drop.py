"""Lumped DC/charge-budget teaching calculations; not a PDN/SPICE solver."""


def dc_rail(source_volts, current_amps, supply_ohms, return_ohms):
    if min(source_volts, current_amps, supply_ohms, return_ohms) < 0:
        raise ValueError('nonnegative DC parameters required')
    total = supply_ohms + return_ohms
    drop = current_amps * total
    return {'drop': drop, 'load_voltage': source_volts - drop,
            'loss_watts': current_amps * current_amps * total}


def allowed_resistance(drop_budget_volts, peak_amps):
    if drop_budget_volts < 0 or peak_amps <= 0:
        raise ValueError('nonnegative budget and positive current required')
    return drop_budget_volts / peak_amps


def ideal_reservoir_capacitance(delta_amps, seconds, drop_budget_volts):
    if min(delta_amps, seconds) < 0 or drop_budget_volts <= 0:
        raise ValueError('nonnegative pulse and positive voltage budget required')
    return delta_amps * seconds / drop_budget_volts
