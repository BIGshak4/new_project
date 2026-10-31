"""Independent exhaustive truth tables and declared timing recurrences; no HDL."""
from __future__ import annotations

import importlib.util
import itertools
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("batch20_combinational", BANK / "solutions/prep_batch20_combinational.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def check_all():
    results = {}
    for heat, oil in itertools.product((0, 1), repeat=2):
        assert model.fault_alert(heat, oil) == int(any((heat, oil)))
    results["PREP-213"] = {"status": "pass", "exhaustive_rows": 4,
                           "scope": "Active-high functional Boolean alert, not a safety system"}
    count = 0
    for inputs in itertools.product((0, 1), repeat=4):
        for s1, s0 in itertools.product((0, 1), repeat=2):
            index = 2 * s1 + s0
            assert model.mux4_source(*inputs, s1, s0) == inputs[3 - index]
            assert model.mux4_standard(*inputs, s1, s0) == inputs[index]
            count += 1
    results["PREP-214"] = {"status": "pass", "exhaustive_source_rows": count,
                           "exhaustive_standard_rows": count, "source_selected_inputs": ["Q3", "Q2", "Q1", "Q0"],
                           "mux_count": 3, "data_path_mux_levels": 2,
                           "scope": "All input/select tuples; no physical timing measurement"}
    for a, b, c in itertools.product((0, 1), repeat=3):
        s, carry = model.full_adder(a, b, c)
        assert s + 2 * carry == a + b + c
    count = 0
    for a in range(4):
        for b in range(16):
            expected = a + b
            assert model.add_2_to_4_ripple(a, b) == expected
            assert model.add_2_to_4_carry_select(a, b) == expected
            assert model.zero_delay_mux_add(a, b) == expected
            count += 1
    # Independent arrival-time recurrence: both FA outputs arrive one ns after
    # the latest data/carry input. Tied constants and wires take zero time.
    carry, ripple_sums = 0, []
    for _ in range(4):
        carry = max(0, 0, carry) + 1
        ripple_sums.append(carry)
    assert max(*ripple_sums, carry) == 4
    lower_carry = max(0, max(0, 0, 0) + 1) + 1
    upper_candidate = max(0, max(0, 0, 0) + 1) + 1
    carry_select = max(lower_carry, upper_candidate)  # zero-delay output MUX
    assert carry_select == 2
    assert max(a + b for a in range(4) for b in range(16)) == 18
    assert 18 >= 2**4 and 18 < 2**5
    results["PREP-215"] = {"status": "pass", "full_adder_rows": 8,
                           "exhaustive_operand_pairs_per_architecture": count, "architectures": 3,
                           "maximum_unsigned_sum": 18, "minimum_result_width": 5,
                           "ripple_fa_count": 4, "ripple_delay_ns": 4,
                           "carry_select_fa_count": 6, "carry_select_delay_ns": 2,
                           "unrestricted_zero_delay_mux_tree_delay_ns": 0,
                           "scope": "Exact arithmetic and stated unit-FA/zero-MUX timing model; no synthesis"}
    for a, b in itertools.product((0, 1), repeat=2):
        g = model.mux_gates(a, b)
        assert g == {"not_b": int(not b), "and": int(bool(a) and bool(b)),
                     "or": int(bool(a) or bool(b)), "xor": int(a != b),
                     "nand": int(not (a and b))}
    results["PREP-070"] = {"status": "pass", "exhaustive_operand_rows": 4,
                           "function_assertions": 20, "scope": "Four-gate bundle plus shared MUX inverter"}
    for q, data, enable in itertools.product((0, 1), repeat=3):
        assert model.latch_step(q, data, enable) == (data if enable else q)
    steps = 0
    for initial_m, initial_q in itertools.product((0, 1), repeat=2):
        for trace in itertools.product((0, 1), repeat=8):
            m, q, prev_clock = initial_m, initial_q, 1
            expected_q = initial_q
            for index, data in enumerate(trace):
                clock = index % 2
                if prev_clock == 0 and clock == 1:
                    expected_q = trace[index - 1]
                m, q = model.master_slave_step(m, q, data, clock)
                assert q == expected_q
                prev_clock = clock
                steps += 1
    # Repeated settled updates within one phase show latch transparency/hold.
    phase_checks = 0
    for m, q, clock in itertools.product((0, 1), repeat=3):
        for data0, data1 in itertools.product((0, 1), repeat=2):
            m0, q0 = model.master_slave_step(m, q, data0, clock)
            m1, q1 = model.master_slave_step(m0, q0, data1, clock)
            assert (q0, q1) == ((q, q) if clock == 0 else (m, m))
            assert (m0, m1) == ((data0, data1) if clock == 0 else (m, m))
            phase_checks += 1
    results["PREP-083"] = {"status": "pass", "latch_rows": 8,
                           "master_slave_trace_steps": steps, "stable_phase_checks": phase_checks,
                           "scope": "Settled ideal model, known initial states; no setup/hold, overlap or analog verification"}
    count = 0
    for word in range(1 << 20):
        # Independent oracle: find the first '1' scanning the string from LSB.
        bits = f"{word:020b}"[::-1]
        expected = 0 if "1" not in bits else 1 << bits.index("1")
        assert model.isolate_lsb_serial(word) == expected
        assert model.isolate_lsb_balanced(word) == expected
        count += 1
    # Independently count OR-tree levels by repeated pairwise reduction.
    arrivals = [0]
    for size in range(1, 20):
        values = [0] * size
        while len(values) > 1:
            values = [max(values[i:i + 2]) + 1 if len(values[i:i + 2]) == 2 else values[i]
                      for i in range(0, len(values), 2)]
        arrivals.append(values[0] + 2)
    assert arrivals == model.lsb_arrival_times(20, True)
    assert max(arrivals) == 7 and max(model.lsb_arrival_times(20, False)) == 20
    results["PREP-107"] = {"status": "pass", "exhaustive_20_bit_words_per_network": count,
                           "networks": 2, "serial_delay_ns": 20, "balanced_delay_bound_ns": 7,
                           "timing_outputs_checked": 20,
                           "scope": "Unary NOT and 2-input AND/OR unit-delay abstraction, free wires/fanout; no physical optimality claim"}
    count = 0
    for width in range(1, 9):
        for a in range(1 << width):
            for b in range(1 << width):
                expected = int(a > b)
                assert model.unsigned_gt_mux(a, b, width) == expected
                assert model.unsigned_gt_gate_tree(a, b, width) == expected
                count += 1
    for a, b in itertools.product((0, 1), repeat=2):
        assert model.one_bit_gt_lt(a, b) == (int(a > b), int(a < b))
    results["PREP-110"] = {"status": "pass", "exhaustive_unsigned_operand_pairs_per_network": count,
                           "widths": list(range(1, 9)), "networks": 2, "authorized_one_bit_completion_rows": 4,
                           "scope": "Strict unsigned comparison including every equal pair; no source reconstruction claim"}
    return results


if __name__ == "__main__":
    for ident, result in check_all().items():
        path = BANK / f"checks/{ident.lower()}-batch20-verification.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{ident}: {result['status']}")
