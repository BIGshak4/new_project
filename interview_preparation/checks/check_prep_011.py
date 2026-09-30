"""Exhaustive functional check and zero/one-MUX lower bound."""
from itertools import product
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_011_mux_function import mux, part_a, part_b

if __name__ == '__main__':
    cases=list(product((0,1),repeat=3))
    expected=tuple(int(not(a and b and not c)) for a,b,c in cases)
    for name,fun in [('part_a',part_a),('part_b',part_b)]:
        assert tuple(fun(*case) for case in cases)==expected, name
    sources={'0':(0,)*8,'1':(1,)*8}
    sources.update({name:tuple(case[i] for case in cases) for i,name in enumerate('abc')})
    assert expected not in sources.values()  # no cell, just a wire or constant
    checked=0
    for s,i0,i1 in product(sources,repeat=3):
        output=tuple(mux(x,y,z) for x,y,z in zip(sources[s],sources[i0],sources[i1]))
        assert output!=expected, (s,i0,i1)
        checked+=1
    assert checked==125
    assert expected==(1,1,1,1,1,1,0,1)
    print('PASS: both constructions match all 8 inputs; none of 125 one-MUX wirings or 5 direct outputs realizes f. Two MUXes are minimal under raw-input/constant-only model.')
