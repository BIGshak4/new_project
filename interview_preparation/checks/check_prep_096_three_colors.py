"""Independent true-hat comparison of strategies with restricted local views."""
import importlib.util
import json
import random
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hats096variant", BANK / "solutions/prep_096_three_color_line_hats.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def check_world(hats):
    n = len(hats)
    pairs, pair_correct = model.simulate(hats, "pairs")
    modulo, modulo_correct = model.simulate(hats, "modulo_three")
    assert all(pair_correct[j] for j in range(1, n, 2))
    assert all(modulo_correct[1:])
    assert sum(pair_correct) >= n // 2 and sum(modulo_correct) >= n - 1
    assert all(0 <= answer < 3 for answer in pairs + modulo)
    if n >= 2:
        signals, guaranteed = model.simulate(hats, "two_parities")
        assert all(guaranteed[2:]) and sum(guaranteed) >= n - 2
        # Independent category check of the two initial information messages.
        target = hats[:-2]
        assert signals[:2] == (sum(c == 0 for c in target) % 2, sum(c == 1 for c in target) % 2)
    return sum(modulo_correct)


def run_checks():
    worlds = 0
    minimum = {}
    for n in range(1, 9):
        minimum[n] = n
        for hats in product(range(3), repeat=n):
            minimum[n] = min(minimum[n], check_world(hats))
            worlds += 1
        assert minimum[n] == n - 1
    rng = random.Random(9603)
    for _ in range(1000):
        check_world(tuple(rng.randrange(3) for _ in range(100)))
    indistinguishable = 0
    for visible in product(range(3), repeat=5):
        first_messages = {model.simulate(visible + (own,), "modulo_three")[0][0] for own in range(3)}
        assert len(first_messages) == 1
        indistinguishable += 1
    return {"question_id": "PREP-096", "variant": "three_color_stages", "status": "passed",
            "all_ternary_worlds_lengths_one_through_eight": worlds, "seeded_hundred_person_worlds": 1000,
            "indistinguishable_first_speaker_view_classes": indistinguishable,
            "modulo_strategy_worst_correct_n1_through_n8": minimum,
            "scope": "All small ternary assignments and seeded n=100 worlds tested. Each reply receives visible hats and heard replies only. General 99-person guarantee and upper bound are proved, not inferred from random trials."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-096-three-colors-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
