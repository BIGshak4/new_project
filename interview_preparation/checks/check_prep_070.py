"""Exhaustive Boolean MUX/AND verification."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / 'solutions'))
from prep_070_and_mux import and_from_mux, mux


def main():
    for s, d0, d1 in itertools.product(range(2), repeat=3):
        assert mux(s, d0, d1) == ((1 - s) & d0) | (s & d1)
    for a, b in itertools.product(range(2), repeat=2):
        assert and_from_mux(a, b) == a * b
        assert mux(b, 0, a) == a * b
    evidence = {'question_id': 'PREP-070', 'status': 'passed', 'mux_rows': 8,
                'and_rows': 4, 'symmetric_wiring_rows': 4,
                'scope': 'Exhaustive ideal Boolean truth table, not timing/synthesis/hardware testing.'}
    (BANK / 'checks/prep-070-verification.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
