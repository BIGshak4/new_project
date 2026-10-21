"""Enumerate every input for both branch-only stuck-at faults."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / 'solutions'))
from prep_069_branch_fault import output


def main():
    rows = []
    for a, b, c in itertools.product(range(2), repeat=3):
        clean, sa0, sa1 = (output(a, b, c, fault) for fault in (None, 0, 1))
        assert clean == int(a == 1 and b == 0 and c == 0)
        assert sa0 == clean and sa1 == 0
        rows.append({'A': a, 'B': b, 'C': c, 'fault_free': clean, 'sa0': sa0, 'sa1': sa1})
    detected = [(r['A'], r['B'], r['C']) for r in rows if r['fault_free'] != r['sa1']]
    assert detected == [(1, 0, 0)]
    evidence = {'question_id': 'PREP-069', 'status': 'passed', 'input_combinations': 8,
                'circuit_evaluations': 24, 'sa1_test': [1, 0, 0], 'sa0_detectable': False,
                'truth_table': rows, 'scope': 'Exact binary combinational model of NOR input branch fault. No physical fault injection or analogue timing.'}
    (BANK / 'checks/prep-069-verification.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
