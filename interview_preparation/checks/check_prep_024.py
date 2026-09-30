"""Verify counting against explicit paths and a combinatorial expression."""
import sys
from math import comb
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_024_grasshopper_stairs import count_ways, count_ways_fast


def paths(n):
    if n == 0:
        yield ()
    for step in (1, 2):
        if step <= n:
            for rest in paths(n - step):
                yield (step,) + rest


for n in range(17):
    actual = list(paths(n))
    assert len(actual) == len(set(actual))
    assert all(sum(p) == n for p in actual)
    assert len(actual) == count_ways(n) == count_ways_fast(n)
for n in range(301):
    expected = sum(comb(n - doubles, doubles) for doubles in range(n // 2 + 1))
    assert count_ways(n) == count_ways_fast(n) == expected
for n in [1000, 10000]:
    assert count_ways(n) == count_ways_fast(n)
for fun in (count_ways, count_ways_fast):
    for n in [-1, 1.5, True]:
        try:
            fun(n)
        except ValueError:
            pass
        else:
            raise AssertionError(n)
assert [count_ways(n) for n in range(6)] == [1, 1, 2, 3, 5, 8]
print('PASS: enumerated every path for n=0..16; 301 binomial-sum comparisons; n=1000/10000 cross-checks; invalid-input checks.')
