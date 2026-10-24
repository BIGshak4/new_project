"""Independent world enumeration and invisible-own-hat pairing for PREP-096."""
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hats', ROOT / 'solutions/prep_096_line_hats_parity.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def main():
    worlds = correct_replies = indistinguishable_pairs = 0
    for size in range(1, 15):
        for world in range(1 << size):
            hats = [(world >> index) & 1 for index in range(size)]
            answers = model.simulate(hats)
            assert answers[0] == sum(hats[:-1]) % 2
            assert answers[1:] == list(reversed(hats[:-1]))
            assert sum(a == b for a, b in zip(answers, reversed(hats), strict=True)) >= size - 1
            worlds += 1
            correct_replies += size - 1
        for visible in range(1 << (size - 1)):
            hats = [(visible >> index) & 1 for index in range(size - 1)]
            a = model.simulate(hats + [0])
            b = model.simulate(hats + [1])
            assert a == b and (a[0] == 0) != (b[0] == 1)
            indistinguishable_pairs += 1
    rng = random.Random(96)
    for _ in range(120):
        size = rng.choice([1, 2, 17, 101, 257, 1024])
        hats = [rng.randrange(2) for _ in range(size)]
        before = hats[:]
        answers = model.simulate(hats)
        assert hats == before and answers[1:] == list(reversed(hats[:-1]))
    for hats in ([], [2], [-1], [0, 1, 3]):
        try:
            model.simulate(hats)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid binary-color world accepted')
    result = {'question_id': 'PREP-096', 'exhaustive_worlds': worlds, 'correct_nonfirst_replies': correct_replies,
              'invisible_own_hat_pairs': indistinguishable_pairs, 'seeded_worlds': 120,
              'maximum_sample_size': 1024, 'invalid_world_rejections': 4,
              'scope': 'Python local-information model; proof of all-n correctness and optimal worst-case guarantee is separate.'}
    (ROOT / 'checks/prep-096-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
