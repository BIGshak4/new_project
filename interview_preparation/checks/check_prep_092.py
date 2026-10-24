"""Truth-table check plus all topologically ordered NAND networks of <=3 gates."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / 'solutions'))
from prep_092_xor_nand import xor_from_nand

rows = []
for a, b in itertools.product((False, True), repeat=2):
    result = xor_from_nand(a, b)
    assert result == (a != b)
    rows.append({'A': int(a), 'B': int(b), 'Y': int(result)})

# Each integer packs all four input assignments: bit 0=00,1=01,2=10,3=11.
# A=1100, B=1010, XOR=0110. Select any pair of preceding wires, with
# repetitions and arbitrary fanout. Every finite acyclic network has such an order.
target = 0b0110
counts = [0, 0, 0]


def explore(wires, depth):
    if depth == 3:
        return
    for i in range(len(wires)):
        for j in range(i, len(wires)):
            out = (~(wires[i] & wires[j])) & 0b1111
            counts[depth] += 1
            assert out != target
            explore(wires + (out,), depth + 1)


assert target not in (0b1100, 0b1010)
explore((0b1100, 0b1010), 0)
record = {
    'question_id': 'PREP-092', 'checked_on': '2026-10-24', 'status': 'passed',
    'truth_table': rows, 'one_two_three_gate_network_counts': counts,
    'lower_bound_scope': 'Acyclic combinational networks of two-input NAND gates; only uncomplemented A,B as external inputs; tied pins and unrestricted fanout allowed; output any gate wire; no free constants or inversion.',
    'oracle': 'a!=b for construction; exhaustive four-row truth-vector propagation for every <=3-gate DAG topology in the stated model.',
    'scope': 'Steady-state Boolean model; no HDL compilation, physical delay, hazard or transistor-area verification.'
}
(BANK / 'checks/prep-092-verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
