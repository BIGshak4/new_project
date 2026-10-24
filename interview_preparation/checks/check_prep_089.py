"""Compare one-pass multiplicity counting with independent index enumeration."""
import itertools
import json
import random
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / 'solutions'))
from prep_089_count_pairs import count_pairs


def oracle(values, target):
    return sum(values[i] + values[j] == target
               for i in range(len(values)) for j in range(i + 1, len(values)))


exhaustive = 0
for length in range(7):
    for values in itertools.product(range(-2, 4), repeat=length):
        for target in range(-4, 7):
            assert count_pairs(values, target) == oracle(values, target)
            exhaustive += 1
rng = random.Random(891024)
for _ in range(400):
    values = [rng.randrange(-20, 21) for _ in range(rng.randrange(101))]
    target = rng.randrange(-40, 41)
    before = values[:]
    expected = oracle(values, target)
    assert count_pairs(values, target) == expected
    assert values == before
    assert count_pairs(iter(values), target) == expected
    rng.shuffle(values)
    assert count_pairs(values, target) == expected
    shifted = [v + 9 for v in values]
    assert count_pairs(shifted, target + 18) == expected
assert count_pairs([1, 4, 1, 4, 2, 3], 5) == 5
assert count_pairs([0] * 10000, 0) == 10000 * 9999 // 2
assert count_pairs([2, 2, 2], 4) == 3
assert count_pairs([5], 10) == 0
record = {
    'question_id': 'PREP-089', 'checked_on': '2026-10-24', 'status': 'passed',
    'exhaustive_array_target_cases': exhaustive, 'seeded_random_cases': 400,
    'single_pass_iterators': True, 'permutation_and_translation_invariance': True,
    'large_duplicate_case_length': 10000, 'input_unchanged': True,
    'oracle': 'Independent enumeration of every i<j index pair; no frequency dictionary in oracle.',
    'scope': 'Exact integer promised inputs; no hash-table worst-case or fixed-width overflow benchmark.'
}
(BANK / 'checks/prep-089-verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
