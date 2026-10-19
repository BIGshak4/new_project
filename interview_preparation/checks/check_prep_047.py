"""Exhaust truth rows and all <=3-gate DAGs in the stated A-only grammar."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "threshold_network", ROOT / "solutions/prep_047_threshold_three_of_four.py"
)
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def gate_signature(pins):
    """Evaluate A on all 16 rows by six pairwise bitwise intersections."""
    a, b, c, d = pins
    return (a & b) | (a & c) | (a & d) | (b & c) | (b & d) | (c & d)


def exhaustive_lower_bound():
    # Bit i denotes truth row abcd = the four-bit representation of i.
    sources = (0, 0xFFFF) + tuple(
        sum(1 << row for row in range(16) if (row >> shift) & 1)
        for shift in (3, 2, 1, 0)
    )
    target = sum(1 << row for row in range(16) if row.bit_count() >= 3)
    assert target not in sources
    states = {()}
    coverage = []
    tested_patterns = 0
    for gate_count in (1, 2, 3):
        next_states = set()
        distinct_outputs = set()
        pin_patterns = 0
        for state in states:
            available = sources + state
            # A is symmetric, so one representative of each pin multiset suffices.
            # Repetition is allowed, as are constants and fanout of all old wires.
            for pins in itertools.combinations_with_replacement(available, 4):
                pin_patterns += 1
                output = gate_signature(pins)
                distinct_outputs.add(output)
                assert output != target, (gate_count, state, pins)
                # A function already available can be replaced by that wire at
                # no cost. A minimum circuit has no duplicate-function gate.
                if gate_count < 3 and output not in available:
                    next_states.add(tuple(sorted(state + (output,))))
        coverage.append({
            "final_gate_number": gate_count,
            "available_signal_sets_before_final_gate": len(states),
            "pin_multisets_tested": pin_patterns,
            "distinct_final_functions": len(distinct_outputs),
            "target_found": False,
        })
        tested_patterns += pin_patterns
        states = next_states
    assert [row["available_signal_sets_before_final_gate"] for row in coverage] == [1, 33, 948]
    assert tested_patterns == 319896
    return {
        "zero_gate_source_functions_checked": len(sources),
        "target_signature_hex": f"0x{target:04x}",
        "pin_multisets_tested_total": tested_patterns,
        "layers": coverage,
        "minimum_a_gates": 4,
        "completeness_argument": (
            "Topologically order an acyclic candidate. Retain all previous gate truth "
            "functions, allowing arbitrary fanout. Skip only gates whose complete truth "
            "function is already available, since they can be replaced by that wire. "
            "Merge states with identical available function sets; later gates depend "
            "only on those functions, not on the order of their creation. Symmetry of "
            "A makes pin multisets exhaustive, including repeated signals and constants. "
            "Thus every candidate with at most three A gates has a representative."
        ),
    }


def verify():
    truth_rows = []
    primitive_rows = 0
    for bits in itertools.product((0, 1), repeat=4):
        expected_primitive = int(sum(bits) >= 2)
        assert MODEL.threshold_a(*bits) == expected_primitive
        masks = tuple(0xFFFF if bit else 0 for bit in bits)
        assert gate_signature(masks) == (0xFFFF if expected_primitive else 0)
        primitive_rows += 1
        a, b, c, d = bits
        p, q, r, y = MODEL.netlist_values(*bits)
        expected = int(sum(bits) >= 3)
        assert p == (c & d)
        assert q == (c | d)
        assert r == int(a + b + (c & d) >= 2)
        assert y == expected == MODEL.three_of_four(*bits)
        # Independent specification for the free-inversion alternative.
        assert 1 - MODEL.threshold_a(1-a, 1-b, 1-c, 1-d) == expected
        truth_rows.append({"abcd": "".join(map(str, bits)), "p": p, "q": q, "r": r, "y": y})
    invalid_cases = 0
    for invalid in (-1, 2, None, "1"):
        try:
            MODEL.three_of_four(invalid, 0, 1, 0)
        except ValueError:
            invalid_cases += 1
        else:
            raise AssertionError("Nonbinary input accepted")
    synthesis = exhaustive_lower_bound()
    return {
        "question": "PREP-047", "status": "passed",
        "primitive_truth_rows": primitive_rows,
        "construction_truth_rows": len(truth_rows),
        "free_inversion_alternative_rows": len(truth_rows),
        "invalid_input_cases": invalid_cases,
        "truth_rows": truth_rows,
        "truth_rows_sha256": hashlib.sha256(json.dumps(truth_rows, sort_keys=True).encode()).hexdigest(),
        "synthesis": synthesis,
        "cost_model": "Only A gates plus free 0/1 constants, direct wires, fanout and repeated pins; no inversion or other gates; acyclic combinational circuits.",
        "scope": "Exact Boolean function and gate-count verification under this grammar. No HDL simulation, synthesis, transistor area, physical delay or glitch-freedom claim. Minimum changes if free inversion is permitted; constants were not explicit in the source.",
    }


if __name__ == "__main__":
    result = verify()
    path = ROOT / "checks/prep-047-verification.json"
    path.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8"))
    print(json.dumps({"status": result["status"], "truth_rows": result["construction_truth_rows"], "minimum_a_gates": result["synthesis"]["minimum_a_gates"], "pin_multisets": result["synthesis"]["pin_multisets_tested_total"]}))
