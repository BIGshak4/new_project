"""Exhaustive missing pairs and independent set/sum-square verification."""
import itertools
import json
import random
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / 'solutions'))
from prep_088_two_missing_zero_based import missing_two_zero_based


def oracle(values):
    upper = len(values) + 1
    total = upper * (upper + 1) // 2 - sum(values)
    squares = upper * (upper + 1) * (2 * upper + 1) // 6 - sum(v * v for v in values)
    import math
    difference = math.isqrt(2 * squares - total * total)
    assert difference * difference == 2 * squares - total * total
    return ((total - difference) // 2, (total + difference) // 2)


def check(values, expected):
    before = tuple(values)
    assert missing_two_zero_based(values) == expected == oracle(values)
    assert tuple(values) == before


cases = 0
for length in range(17):
    for missing in itertools.combinations(range(length + 2), 2):
        remaining = [v for v in range(length + 2) if v not in missing]
        for arranged in (remaining, list(reversed(remaining)), remaining[1:] + remaining[:1]):
            check(arranged, missing)
            cases += 1
permutations = 0
for length in range(6):
    for missing in itertools.combinations(range(length + 2), 2):
        remaining = [v for v in range(length + 2) if v not in missing]
        for arranged in itertools.permutations(remaining):
            check(arranged, missing)
            permutations += 1
rng = random.Random(88022)
for _ in range(300):
    length = rng.randrange(0, 5001)
    missing = tuple(sorted(rng.sample(range(length + 2), 2)))
    remaining = [v for v in range(length + 2) if v not in missing]
    rng.shuffle(remaining)
    check(remaining, missing)
record = {'question_id': 'PREP-088', 'checked_on': '2026-10-22', 'status': 'passed',
          'missing_pair_order_cases': cases, 'all_small_permutations': permutations,
          'seeded_random_cases': 300, 'maximum_random_length': 5000,
          'zero_inclusive_domain': True, 'input_unchanged': True,
          'oracle': 'Independent exact sums and sums-of-squares with integer square root; expected omitted pair also constructed separately.',
          'scope': 'Valid promised repeatable inputs only. Test harness uses extra storage; solution does not. Python word-count analysis, not a fixed-width compilation or benchmark.'}
(BANK / 'checks/prep-088-verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
