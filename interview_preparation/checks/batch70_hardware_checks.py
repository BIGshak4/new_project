"""Independent bounded arithmetic, history, ODE and observability checks."""

import ast
import importlib.util
import itertools
import math
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def load(stem):
    spec = importlib.util.spec_from_file_location(stem, BANK / "solutions" / (stem + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[stem] = module
    spec.loader.exec_module(module)
    return module


def lc():
    model = load("prep_170_switched_ideal_lc")
    samples = 0
    for inductance, capacitance, v0 in (
        (1.0, 1.0, 2.0),
        (0.2, 0.05, 3.3),
        (0.002, 0.000001, 5.0),
        (2.0, 0.25, -2.0),
    ):
        period = 2 * math.pi * math.sqrt(inductance * capacitance)
        dt = period / 1000
        v, i = v0, 0.0

        def slope(state, capacitance=capacitance, inductance=inductance):
            return -state[1] / capacitance, state[0] / inductance

        for tick in range(4001):
            exact_v, exact_i = model.response(tick * dt, inductance, capacitance, v0)
            assert abs(v - exact_v) < 1e-7 * max(1, abs(v0))
            assert abs(i - exact_i) < 1e-7 * max(1, abs(v0) * math.sqrt(capacitance / inductance))
            energy = capacitance * exact_v**2 / 2 + inductance * exact_i**2 / 2
            assert math.isclose(energy, capacitance * v0**2 / 2, rel_tol=1e-12)
            k1 = slope((v, i))
            k2 = slope((v + dt * k1[0] / 2, i + dt * k1[1] / 2))
            k3 = slope((v + dt * k2[0] / 2, i + dt * k2[1] / 2))
            k4 = slope((v + dt * k3[0], i + dt * k3[1]))
            v += dt * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]) / 6
            i += dt * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]) / 6
            samples += 1
        quarter_v, quarter_i = model.response(period / 4, inductance, capacitance, v0)
        assert abs(quarter_v) < 1e-12 * max(1, abs(v0))
        assert math.isclose(quarter_i, v0 * math.sqrt(capacitance / inductance), rel_tol=1e-12)
    return {
        "status": "passed",
        "independent_rk4_trajectories": 4,
        "trajectory_samples": samples,
        "energy_checks": samples,
        "scope": "Analytic ideal LC versus independent RK4 integration over four periods; no losses, SPICE, switching impulse or physical circuit validation.",
    }


def run_oracle(bits):
    outputs = []
    for index, bit in enumerate(bits):
        if index == 0 or bit == bits[index - 1]:
            outputs.append(0)
            continue
        previous = bits[index - 1]
        start = index - 1
        while start >= 0 and bits[start] == previous:
            start -= 1
        length = index - 1 - start
        outputs.append(int((previous == 0 and length % 2 == 0) or (previous == 1 and length % 2 == 1)))
    return outputs


def distinct_pairs(table):
    count = 0
    for a, b in itertools.combinations(table, 2):
        found = False
        for length in range(1, 5):
            for word in itertools.product((0, 1), repeat=length):
                first, second = a, b
                out1, out2 = [], []
                for bit in word:
                    first, value = table[first][bit]
                    out1.append(value)
                    second, value = table[second][bit]
                    out2.append(value)
                if out1 != out2:
                    found = True
                    break
            if found:
                break
        assert found, (a, b)
        count += 1
    return count


def completed_runs():
    model = load("prep_171_completed_run_parity")
    words = samples = resets = 0
    for length in range(13):
        for word in itertools.product((0, 1), repeat=length):
            assert model.detect(word) == run_oracle(word)
            words += 1
            samples += length
    for events in itertools.product(range(4), repeat=6):
        state, history = model.RESET_STATE, []
        for event in events:
            bit, reset = event & 1, bool(event >> 1)
            state, error = model.step(state, bit, reset=reset)
            if reset:
                history = []
                assert error == 0
            else:
                history.append(bit)
                assert error == run_oracle(history)[-1]
        resets += 1
    assert model.detect([int(x) for x in "000011111000001"]) == [int(x) for x in "000010000100000"]
    assert model.detect([0]) == [0] and model.detect([1]) == [0]
    return {
        "status": "passed",
        "exhaustive_words": words,
        "accepted_bits": samples,
        "reset_streams": resets,
        "distinguished_history_state_pairs": distinct_pairs(model.TABLE),
        "scope": "Finite Python event model versus full-history run-length oracle; source example exact. Four Mealy history states distinguishable; no physical timing or automatic end-of-stream flush.",
    }


def led():
    model = load("prep_172_two_switch_led")
    rows = toggles = 0
    for a, b in itertools.product((0, 1), repeat=2):
        initial = model.xor_led(a, b)
        assert initial == int(a != b)
        assert model.traveler_path(a, b) == 1 - initial
        for position in range(2):
            changed = [a, b]
            changed[position] ^= 1
            assert model.xor_led(*changed) == 1 - initial
            assert model.traveler_path(*changed) != model.traveler_path(a, b)
            toggles += 1
        assert model.xor_led(a ^ 1, b ^ 1) == initial
        rows += 1
    assert math.isclose(model.current_limit(3.3, 2.0, 0.002), 650.0)
    return {
        "status": "passed",
        "truth_rows": rows,
        "single_switch_toggles": toggles,
        "double_switch_cases": 4,
        "resistor_example_ohms": 650,
        "scope": "Settled Boolean XOR/XNOR and ideal current-limit arithmetic only. No mechanical bounce, hazards, LED/device characteristics, mains wiring or physical test.",
    }


def sequence1011():
    model = load("prep_173_overlapping_1011")
    words = samples = reset_streams = 0

    def oracle(history):
        return int(len(history) >= 4 and history[-4:] == [1, 0, 1, 1])

    for length in range(13):
        for word in itertools.product((0, 1), repeat=length):
            expected = [oracle(list(word[: index + 1])) for index in range(length)]
            assert model.detections(word) == expected
            words += 1
            samples += length
    for events in itertools.product(range(4), repeat=6):
        state, history = 0, []
        for event in events:
            bit, reset = event & 1, bool(event >> 1)
            state, out = model.step(state, bit, reset=reset)
            if reset:
                history = []
                assert out == 0
            else:
                history.append(bit)
                assert out == oracle(history)
        reset_streams += 1
    assert model.detections([int(x) for x in "1011011"]) == [0, 0, 0, 1, 0, 0, 1]
    return {
        "status": "passed",
        "exhaustive_words": words,
        "accepted_bits": samples,
        "reset_streams": reset_streams,
        "distinguished_prefix_state_pairs": distinct_pairs(model.TABLE),
        "scope": "Mealy transition events versus independent full-history suffix comparison; overlap and reset checked. No HDL, combinational glitch or physical timing claim.",
    }


def square():
    model = load("prep_174_two_bit_unsigned_square")
    for value in range(4):
        assert model.square(value) == value * value
        assert 0 <= model.square(value) < 16
    rejected = 0
    for value in (-1, 4, True, "2"):
        try:
            model.square(value)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(value)
    return {
        "status": "passed",
        "all_input_rows": 4,
        "malformed_inputs_rejected": rejected,
        "scope": "Exact unsigned two-bit gate equations versus integer square. No synthesis, gate minimum or signed-input claim.",
    }


def toggle():
    model = load("prep_119_four_seven_constraints")
    functions = (model.conditional, model.addition_subtraction, model.without_add_subtract_if, model.xor_only)
    for function in functions:
        assert [function(x) for x in (4, 7)] == [7, 4]
        assert all(function(function(x)) == x for x in (4, 7))
    tree = ast.parse((BANK / "solutions/prep_119_four_seven_constraints.py").read_text("utf-8"))
    funcs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    for name in ("addition_subtraction", "without_add_subtract_if", "xor_only"):
        assert not any(isinstance(n, (ast.If, ast.IfExp, ast.Compare)) for n in ast.walk(funcs[name]))
    assert {type(n.op) for n in ast.walk(funcs["addition_subtraction"]) if isinstance(n, ast.BinOp)} == {
        ast.Sub
    }
    assert not any(isinstance(n, (ast.Add, ast.Sub)) for n in ast.walk(funcs["without_add_subtract_if"]))
    assert {type(n.op) for n in ast.walk(funcs["xor_only"]) if isinstance(n, ast.BinOp)} == {ast.BitXor}
    return {
        "status": "passed",
        "legal_input_function_cases": 8,
        "involution_cases": 8,
        "restricted_function_asts": 3,
        "scope": "Promised 4/7 input mapping and AST restrictions. Original duplicate 4-to7 statement archived; reverse 7-to4 is an explicit editorial assumption.",
    }


def gate_step():
    model = load("prep_115_gate_step_switch_illustration")
    cases = samples = 0
    for supply, pullup, ron, cap in itertools.product(
        (3.3, 5.0), (1000.0, 10000.0), (100.0, 1000.0), (1e-10, 1e-9)
    ):
        tau = (pullup * ron / (pullup + ron)) * cap
        dt = tau / 200
        value = supply

        def derivative(v, supply=supply, pullup=pullup, ron=ron, cap=cap):
            return ((supply - v) / pullup - v / ron) / cap

        previous = supply + 1
        for tick in range(1001):
            actual = model.drain_after_gate_turn_on(
                tick * dt, supply=supply, pullup=pullup, on_resistance=ron, load_capacitance=cap
            )
            assert abs(actual - value) < 1e-8 * supply
            assert supply * ron / (pullup + ron) <= actual <= previous
            previous = actual
            k1 = derivative(value)
            k2 = derivative(value + dt * k1 / 2)
            k3 = derivative(value + dt * k2 / 2)
            k4 = derivative(value + dt * k3)
            value += dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
            samples += 1
        cases += 1
    return {
        "status": "passed",
        "explicit_switch_rc_scenarios": cases,
        "independent_rk4_samples": samples,
        "scope": "Only a labelled added NMOS-as-switch/Rpullup/Cout illustration versus independent ODE integration. Does not resolve the original unidentified step-input node or simulate MOS gate charge/SPICE.",
    }


def sensor():
    model = load("prep_053_single_sensor_observability")
    original = load("prep_053_doorway_counter")
    assert model.single_sensor_trace("entry") == model.single_sensor_trace("exit")
    for direction, delta in (("entry", 1), ("exit", -1)):
        counter = original.DoorwayCounter(count=4, maximum=8)
        events = [counter.sample(*bits) for bits in model.two_sensor_trace(direction)]
        assert events == [0, 0, 0, 0, delta]
        assert counter.count == 4 + delta and counter.count_valid
    counter = original.DoorwayCounter(count=4, maximum=8)
    assert [counter.sample(*bits) for bits in ((0, 0), (1, 0), (1, 1), (1, 0), (0, 0))] == [0] * 5
    return {
        "status": "passed",
        "one_sensor_indistinguishable_worlds": 2,
        "two_sensor_complete_traversals": 2,
        "cancelled_partial_traversals": 1,
        "scope": "Information counterexample plus unchanged canonical two-sensor model. Count changes at the defined completed-passage boundary, not arbitrary continuous body position; no sensor hardware validation.",
    }


CHECKS = {
    "170": lc,
    "171": completed_runs,
    "172": led,
    "173": sequence1011,
    "174": square,
    "119_four_seven_70": toggle,
    "115_gate_step_70": gate_step,
    "053_single_sensor_70": sensor,
}
