"""Validate the ideal equation model; does not claim RTL simulation."""
from itertools import product
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_010_divide_by_three import simulate


def transitions(rows):
    return [(r['t'], r['out']) for before, r in zip(rows, rows[1:])
            if r['out'] != before['out']]


def check_two_ff_lower_bound():
    # Restricted model: one posedge FF, one negedge FF, arbitrary next-state
    # Boolean functions of their two Q bits and arbitrary output of Q only.
    # Clock phase is external, not an input to output combinational logic.
    # 8 augmented (Q,phase) states => 24 half-edges clear every transient.
    patterns = {tuple(int((i + phase) % 6 < 3) for i in range(24))
                for phase in range(6)}
    checked = 0
    for f, g in product(range(16), repeat=2):
        for initial in range(4):
            a, b = initial >> 1, initial & 1
            states = []
            for edge in range(48):
                state = (a << 1) | b
                if edge % 2 == 0:
                    a = (f >> state) & 1
                else:
                    b = (g >> state) & 1
                states.append((a << 1) | b)
            for output_function in range(16):
                values = tuple((output_function >> s) & 1 for s in states[24:])
                assert values not in patterns, (f, g, initial, output_function)
                checked += 1
    assert checked == 16384
    return checked


if __name__ == '__main__':
    rows = simulate(300)
    assert [r['out'] for r in rows] == [1, 1, 1, 0, 0, 0] * 100
    assert [(r['q1'], r['q0']) for r in rows[::2]] == [(1,0),(0,1),(0,0)] * 100
    for initial in product((0, 1), repeat=3):
        events = transitions(simulate(60, initial=initial))
        stable = [(t, v) for t, v in events if t >= 3]
        assert all(abs(b[0] - a[0] - 1.5) < 1e-9 for a,b in zip(stable, stable[1:]))
    # Confirm (not conceal) dependence on input duty: high=1+d, low=2-d.
    for duty in (0.1, 0.25, 0.5, 0.75, 0.9):
        events = [(t,v) for t,v in transitions(simulate(60, duty)) if t >= 3]
        for (t, value), (next_t, _) in zip(events, events[1:]):
            expected = 1 + duty if value else 2 - duty
            assert abs(next_t - t - expected) < 1e-9
    checked = check_two_ff_lower_bound()
    print(f'PASS: 300 cycles; 8 initial states; 5 input duty ratios; {checked} two-FF truth-table/initial-state cases cannot meet the target under the stated Q-only model. Python model, not HDL simulation.')
