"""Seven-block construction checked against an independent full-sort oracle."""
import importlib.util
import itertools
import json
import random
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sort009',BANK/'solutions/prep_009_five_way_sorter_top_three.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def check(values):
    calls = []
    def block(items):
        assert len(items) == len(set(items)) == 5
        calls.append(tuple(items))
        return sorted(items,reverse=True)
    result = model.top_three(values,block)
    assert result == sorted(values,reverse=True)[:3]
    assert len(calls) == 7


def verify():
    placements = 0
    for positions in itertools.permutations(range(25),3):
        values = [None]*25
        for position,value in zip(positions,(25,24,23),strict=True):
            values[position]=value
        rest = iter(range(1,23))
        values = [next(rest) if value is None else value for value in values]
        check(values)
        placements += 1
    random_cases = 1000
    rng=random.Random(159009)
    for _ in range(random_cases):
        check(rng.sample(range(-100000,100000),25))
    return {'status':'passed','all_top_three_position_placements':placements,'seeded_permutations':random_cases,
            'sorter_calls_per_case':7,'scope':'Functional comparison oracle; minimum-query proof is separate from testing, no synthesized timing/area claim.'}


if __name__ == '__main__':
    result=verify()
    (BANK/'checks/prep-009-sorter-variant-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result)
