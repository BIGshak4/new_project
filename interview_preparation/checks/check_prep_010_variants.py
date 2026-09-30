"""Exhaustive small-state checks for the AND divider and modulo-three counters."""
from itertools import product
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_010_mod3_variants import dff_next, tff_next, adder_next
from prep_010_divide_by_three import simulate

if __name__ == '__main__':
    for q1,q0 in product((0,1),repeat=2):
        assert (1-(q1|q0)) == ((1-q1)&(1-q0))
    for initial in product((0,1),repeat=3):
        q1,q0,delayed=initial
        for row in simulate(30,initial=initial):
            if row['clk']:
                q1,q0=(1-q1)&(1-q0),q1
            else:
                delayed=q1
            assert (q1,q0,delayed,q1|delayed)==tuple(row[k] for k in ('q1','q0','delayed','out'))
    for function in (dff_next,tff_next,adder_next):
        assert function(0,0)==(0,1)
        assert function(0,1)==(1,0)
        assert function(1,0)==(0,0)
        assert function(1,1) in ((0,0),(0,1),(1,0))
        state=(0,0)
        for i in range(120):
            assert (state[0]<<1)|state[1]==i%3
            state=function(*state)
    assert dff_next(1,1)==(1,0)
    assert adder_next(1,1)==(0,0)
    assert tff_next(1,1)==(0,1)
    print('PASS: De Morgan for all 4 states; AND divider matches original for all 8 starts; all 4 states and 120-cycle sequences for DFF/TFF/adder counters. Equation models only.')
