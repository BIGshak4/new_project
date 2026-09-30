"""Exhaust all bounded random-choice paths; do not rely on random sampling."""
import sys
from itertools import product
from math import factorial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_022_random_permutation import random_permutation

paths_checked = 0
for n in range(8):
    bounds = list(range(n, 1, -1))
    outputs = set()
    for choices in product(*(range(1, m + 1) for m in bounds)):
        calls = []
        draws = iter(choices)
        def rand(m):
            calls.append(m)
            return next(draws)
        result = random_permutation(n, rand)
        assert sorted(result) == list(range(1, n + 1))
        assert calls == bounds
        outputs.add(tuple(result))
        paths_checked += 1
    assert len(outputs) == factorial(n)

for n in [8, 100, 1000]:
    for rand in [lambda m: 1, lambda m: m]:
        assert sorted(random_permutation(n, rand)) == list(range(1, n + 1))
for invalid in [-1, 1.5, True]:
    try:
        random_permutation(invalid, lambda m: 1)
    except ValueError:
        pass
    else:
        raise AssertionError(invalid)
for bad in [0, 4, 1.5]:
    try:
        random_permutation(3, lambda m: bad)
    except ValueError:
        pass
    else:
        raise AssertionError(bad)
print(f'PASS: {paths_checked} choice paths for N=0..7; exactly N! distinct permutations for each N; six larger boundary runs and input-contract checks.')
