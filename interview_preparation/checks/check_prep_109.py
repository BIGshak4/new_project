"""Full truth table plus exhaustive small acyclic-network lower bounds."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_109_truth_nand_nor import NAND_NETLIST, NOR_NETLIST, evaluate

truth = (0, 1, 0, 0, 1, 1, 0, 0)
for row, (a, b, c) in enumerate(itertools.product((0, 1), repeat=3)):
    assert evaluate(a, b, c, NAND_NETLIST) == truth[row]
    assert evaluate(a, b, c, NOR_NETLIST) == truth[row]
    assert truth[row] == int(not b and (a or c))
# A truth word stores one complete Boolean function. Enumerate every unordered
# pin pair (including ties) drawn from raw inputs and earlier gate outputs.
input_words = [sum(((row >> shift) & 1) << row for row in range(8)) for shift in (2, 1, 0)]
target = sum(bit << row for row, bit in enumerate(truth))
counts = {}
for family, levels in (("NAND", 3), ("NOR", 1)):
    states = [input_words]
    family_counts = []
    for _ in range(levels):
        next_states = []
        for wires in states:
            for left, right in itertools.combinations_with_replacement(range(len(wires)), 2):
                out = (255 ^ (wires[left] & wires[right])) if family == "NAND" else (255 ^ (wires[left] | wires[right]))
                assert out != target
                next_states.append(wires + [out])
        family_counts.append(len(next_states))
        states = next_states
    counts[family] = family_counts
assert counts == {"NAND": [6, 60, 900], "NOR": [6]}
# Each of A,B,C is essential, so zero gates (one raw wire) or one 2-input gate
# cannot suffice even when the allowed library mixes both families.
for position in range(3):
    assert any(truth[row] != truth[row ^ (1 << (2 - position))] for row in range(8))
record = {
    "question_id": "PREP-109", "checked_on": "2026-10-24", "status": "passed",
    "source_truth_rows": 8, "nand_solution_gates": 4, "nor_solution_gates": 2,
    "exhaustive_too_small_network_counts": counts, "mixed_library_minimum": 2,
    "proof_model": "Acyclic two-input commutative NAND/NOR gates, raw A/B/C only, fanout and tied pins allowed, no free constants/inversions. Every gate is charged, including tied-pin inversion.",
    "scope": "Finite complete small-network enumeration plus constructive circuits and essential-variable lower bound. No transistor-area, arbitrary-fan-in, hazard or physical-delay optimality claim.",
}
(BANK / "checks/prep-109-verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
