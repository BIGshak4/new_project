"""Boolean connectivity and illustrative NMOS voltage limit, not SPICE."""


def nand(a, b):
    return 1 - (a & b)


def gate_mux(a, b, select):
    complement = nand(select, select)
    return nand(nand(a, complement), nand(b, select))


def transmission_gate_mux(a, b, select):
    # TG0 has n-gate !S and p-gate S; TG1 has n-gate S and p-gate !S.
    tg0_on, tg1_on = select == 0, select == 1
    assert tg0_on != tg1_on
    return a if tg0_on else b


def nmos_pass_level(a_volts, b_volts, select, vdd=1.0, threshold=0.25):
    if select not in (0, 1) or not 0 < threshold < vdd:
        raise ValueError("valid binary select and 0 < threshold < vdd required")
    if not 0 <= a_volts <= vdd or not 0 <= b_volts <= vdd:
        raise ValueError("data voltages must lie between the supply rails")
    selected = a_volts if select == 0 else b_volts
    return min(selected, vdd - threshold)


TRANSISTOR_COUNTS = {
    "three_static_cmos_nand2_and_select_inverter": 3 * 4 + 2,
    "two_transmission_gates_and_select_inverter": 2 * 2 + 2,
    "two_nmos_pass_devices_and_cmos_select_inverter": 2 + 2,
    "two_nmos_pass_devices_with_external_complement": 2,
}
