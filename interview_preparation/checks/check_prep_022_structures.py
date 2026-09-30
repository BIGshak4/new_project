"""Check the dictionary and shrinking-array algorithms on every small draw path."""
import sys
from itertools import product
from math import factorial
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_022_random_permutation import permutation_with_array, permutation_with_dict

total = 0
for n in range(8):
    bounds = list(range(n, 1, -1))
    seen = set()
    for choices in product(*(range(1, m + 1) for m in bounds)):
        results = []
        for algorithm in [permutation_with_array, permutation_with_dict]:
            draws = iter(choices)
            calls = []
            def rand(m):
                calls.append(m)
                return next(draws)
            result = tuple(algorithm(n, rand))
            assert calls == bounds
            assert sorted(result) == list(range(1, n + 1))
            results.append(result)
        assert results[0] == results[1]
        seen.add(results[0])
        total += 1
    assert len(seen) == factorial(n)

for algorithm in [permutation_with_array, permutation_with_dict]:
    for n in [8, 100, 1000]:
        for rand in [lambda m: 1, lambda m: m]:
            assert sorted(algorithm(n, rand)) == list(range(1, n + 1))
    for bad_n in [-1, 1.5, True]:
        try:
            list(algorithm(bad_n, lambda m: 1))
        except ValueError:
            pass
        else:
            raise AssertionError(bad_n)
    for bad_rand in [0, 4, 1.5, True]:
        try:
            list(algorithm(3, lambda m: bad_rand))
        except ValueError:
            pass
        else:
            raise AssertionError(bad_rand)
print(f'PASS: {total} draw paths for BOTH algorithms; pathwise equality, N! distinct outputs, all bounds and twelve larger boundary runs verified.')
