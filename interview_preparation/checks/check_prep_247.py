"""Exhaustive bounded inputs, independent set oracle and multiset preservation."""
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('missing_reference', ROOT / 'solutions/prep_247_first_missing_positive.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run():
    count = 0
    for length in range(8):
        for source in itertools.product((-1, 0, 1, 2, 3, 4), repeat=length):
            seen, expected = set(source), 1
            while expected in seen:
                expected += 1
            values = list(source)
            assert module.first_missing_positive(values) == expected
            assert Counter(values) == Counter(source)
            count += 1
    for source in ([1, 2, -4, -1], [3, 4, -1, 1], [1, 1], [0, 0], [2**100, -(2**100)], list(range(1, 1001))):
        values = list(source)
        expected = next(i for i in range(1, len(source) + 2) if i not in source)
        assert module.first_missing_positive(values) == expected
        count += 1
    for source in ([True], ['1'], (1, 2)):
        try:
            module.first_missing_positive(source)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid input accepted')
    result = {'question': 'PREP-247', 'cases': count, 'invalid_cases': 3, 'passed': True,
              'oracle': 'set membership and multiset equality',
              'scope': 'exhaustive length0..7 over six values, plus large and boundary samples; Python executed'}
    (ROOT / 'checks/prep-247-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    print(json.dumps(run()))
