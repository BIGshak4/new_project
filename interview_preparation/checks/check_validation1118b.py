"""Independent oracles for the two verification-design questions."""
from itertools import combinations, product
import json
from pathlib import Path
import random
import sys

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / 'solutions'))
from prep_377_test_selection import choose_tests
from prep_378_memory_partitions import partition


def check_tests():
    faults = set(range(3))
    masks = [set(c) for n in range(4) for c in combinations(faults, n)]
    cases = 0
    for rows in product(masks, repeat=3):
        failures = dict(enumerate(rows))
        for required in masks:
            if not required <= set.union(*rows):
                try:
                    choose_tests(failures, required)
                except ValueError:
                    continue
                raise AssertionError('an uncovered fault was accepted')
            chosen = choose_tests(failures, required)
            assert required <= set().union(*(rows[i] for i in chosen))
            assert len(chosen) == len(set(chosen))
            cases += 1
    assert choose_tests({'A': {1, 2}, 'B': {2}, 'C': {3}}, {1, 2, 3}, ['B']) == ['B','A','C']
    return cases


def check_layouts():
    cases = 0
    for n in range(10):
        for m in range(1, 17):
            for seed in range(51):
                sizes, bases = partition(n, m, None if seed == 0 else random.Random(seed).randint)
                assert len(sizes) == len(bases) == n
                occupied = set()
                for size, base in zip(sizes, bases):
                    assert 0 <= base < m and 0 <= size <= m - base
                    cells = set(range(base, base + size))
                    assert occupied.isdisjoint(cells)
                    occupied |= cells
                if n and seed == 0:
                    assert occupied == set(range(m)) and max(sizes)-min(sizes) <= 1
                cases += 1
    assert partition(0, 0) == ([], [])
    for dims in [(2,0),(-1,3),(0,-1)]:
        try:
            partition(*dims)
        except ValueError:
            continue
        raise AssertionError(dims)
    return cases


if __name__ == '__main__':
    result = {'coverable_cases': check_tests(), 'layout_cases': check_layouts(),
              'scope': 'Deterministic software models checked against unions and independent occupied-cell sets.'}
    path = BANK / 'checks/validation1118b-verification.json'
    path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf8')
    print(result)

