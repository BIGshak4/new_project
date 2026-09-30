"""All sixteen inputs plus exhaustive single-box impossibility."""
from itertools import product
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_013_threshold_or import box, proposed

if __name__ == '__main__':
    cases=list(product((0,1), repeat=4))
    target=tuple(int(any(case)) for case in cases)
    assert box(1,0,1,0)==1 and box(0,0,0,1)==0
    assert tuple(proposed(*case) for case in cases)==target
    sources={'0':(0,)*16,'1':(1,)*16}
    sources.update({name:tuple(case[i] for case in cases) for i,name in enumerate('abcd')})
    assert target not in sources.values()
    checked=0
    for names in product(sources,repeat=4):
        values=tuple(box(*bits) for bits in zip(*(sources[name] for name in names)))
        assert values!=target, names
        checked+=1
    assert checked==1296
    print('PASS: both source examples; all 16 inputs of two-box solution; all 1296 single-box wirings including repeated inputs ruled out; zero-box direct sources ruled out.')
