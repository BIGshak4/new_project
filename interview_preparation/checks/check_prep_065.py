"""Exhaustive finite ideal edge model checks; no HDL simulator is invoked."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / 'solutions'))
from prep_065_dff_from_sr import dff_from_sr, sr_edge


def main():
    for q, d in itertools.product(range(2), repeat=2):
        assert dff_from_sr(q, d) == d
        assert dff_from_sr(q, d, rising=False) == q
    sr_rows = 0
    for q, s, r in itertools.product(range(2), repeat=3):
        assert sr_edge(q, s, r, rising=False) == q
        if s and r:
            try:
                sr_edge(q, s, r)
            except ValueError:
                pass
            else:
                raise AssertionError('11 must be rejected at the edge')
        else:
            assert sr_edge(q, s, r) == ({(0, 0): q, (0, 1): 0, (1, 0): 1}[(s, r)])
        sr_rows += 1
    streams = edges = 0
    for n in range(11):
        for bits in itertools.product(range(2), repeat=n):
            for initial in range(2):
                q = initial
                for d in bits:
                    assert dff_from_sr(q, 1 - d, rising=False) == q
                    q = dff_from_sr(q, d)
                    assert q == d
                    edges += 1
                streams += 1
    evidence = {'question_id': 'PREP-065', 'status': 'passed', 'd_q_combinations': 4,
                'sr_state_input_rows': sr_rows, 'binary_streams_lengths_0_to_10_both_initial_states': streams,
                'rising_edges': edges,
                'scope': 'Ideal Python edge model only; HDL uncompiled, no glitch/timing or physical validation.'}
    (BANK / 'checks/prep-065-verification.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
