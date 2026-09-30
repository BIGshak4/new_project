"""Check sorting, fault localization and all distinct-input ordering classes."""
import sys
from itertools import product, permutations
from math import factorial
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_030_sorter_fault import COMPARATORS, TEST_VECTOR, SIGNATURES, run_network, diagnose

for values in product((-1,0,1,2),repeat=4):
    assert run_network(values)==tuple(sorted(values,reverse=True))
for values in product((0,1),repeat=4):
    assert run_network(values)==tuple(sorted(values,reverse=True))
for fault in (None,1,2,3,4,5):
    observed=run_network(TEST_VECTOR,fault)
    assert observed in SIGNATURES
    assert diagnose(observed)==('healthy' if fault is None else f'C{fault}')
for values in [(10,7,0,-8),(-1,-2,-3,-4),(1000,99,4,0)]:
    outputs=[run_network(values,f) for f in (None,1,2,3,4,5)]
    assert len(set(outputs))==6
    mapped=[tuple(TEST_VECTOR[values.index(v)] for v in output) for output in outputs]
    assert mapped==[run_network(TEST_VECTOR,f) for f in (None,1,2,3,4,5)]
for observed in [(1,2,3,4),(4,4,2,1),(0,0,0,0)]:
    try:
        diagnose(observed)
    except ValueError:
        pass
    else:
        raise AssertionError(observed)
classes={v:len({run_network(v,f) for f in (None,1,2,3,4,5)}) for v in permutations(TEST_VECTOR)}
assert classes[TEST_VECTOR]==6
assert len(COMPARATORS)==5 and 2**4<factorial(4)<=2**5
print('PASS: 256 signed/repeated-value inputs + all 16 binary inputs sorted; all six fault hypotheses uniquely diagnosed by (4,3,2,1); 24 input ordering classes inspected. Functional model only, not HDL or physical timing.')
