"""Additional generic-array source: verify existing Fisher-Yates on objects.

No new shuffle implementation is needed: existing code only swaps references.
Enumerated choice paths are mathematical checks, not RNG quality benchmarks.
"""
from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
from math import factorial
from pathlib import Path

BANK=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('shuffle_existing',BANK/'solutions/prep_022_rand_range_shuffle.py')
module=module_from_spec(spec)
spec.loader.exec_module(module)


def draw_for(choices, expected):
    choices=iter(choices)
    seen=[]
    def draw(low,high):
        seen.append((low,high))
        return next(choices)
    return draw,seen


def run():
    paths=0
    for n in range(8):
        tokens=[object() for _ in range(n)]
        outputs=set()
        ranges=[range(i+1) for i in range(n-1,0,-1)]
        for choices in product(*ranges):
            values=list(tokens)
            before=id(values)
            draw,seen=draw_for(choices,n)
            assert module.shuffle_in_place(values,draw) is None
            assert id(values)==before
            assert sorted(map(id,values))==sorted(map(id,tokens))
            assert seen==[(0,i) for i in range(n-1,0,-1)]
            outputs.add(tuple(map(id,values)))
            paths+=1
        assert len(outputs)==factorial(n)
    duplicates=Counter()
    for choices in product(range(3),range(2)):
        values=['A','A','B']
        draw,_=draw_for(choices,3)
        module.shuffle_in_place(values,draw)
        duplicates[tuple(values)]+=1
    assert len(duplicates)==3 and set(duplicates.values())=={2}
    arbitrary=0
    for original in ([],[None],[{'x':1},[],{'x':1}],['a','a','b'],[None,2,'s',[]]):
        for select_high in (False,True):
            values=list(original)
            before=sorted(map(id,values))
            module.shuffle_in_place(values,lambda lo,hi:hi if select_high else lo)
            assert sorted(map(id,values))==before
            arbitrary+=1
    result=dict(question_id='PREP-022',checked_on='2026-10-21',status='passed_python_model',
                indexed_choice_paths=paths,duplicate_value_paths=6,distinct_duplicate_orders=3,
                arbitrary_object_boundary_cases=arbitrary,
                method='Enumerate indexed permutations for lengths0..7 using identity tokens; verify equal multiplicity for A,A,B and preservation of arbitrary/unhashable objects.',
                limits='Uniformity follows only for conditional-uniform bounded draws. No statistical quality or cryptographic RNG test.')
    (BANK/'checks/prep-022-generic-array-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    run()
