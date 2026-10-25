"""Small complete worlds and all two-player local protocols; seeded ten-color tests."""

import importlib.util
import json
import random
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hats_model", BANK / "solutions/prep_127_distributed_hat_guesses.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def inspect_world(hats):
    guesses = model.simulate_guesses(hats)
    correct = [player for player, (guess, hat) in enumerate(zip(guesses, hats, strict=True)) if guess == hat]
    assert correct == [sum(hats) % len(hats)]


def run_checks():
    worlds = 0
    for n in range(1, 6):
        for hats in product(range(n), repeat=n):
            inspect_world(hats)
            worlds += 1
    rng = random.Random(127)
    ten_color_cases = [(0,) * 10, (9,) * 10, tuple(range(10)), tuple(reversed(range(10)))]
    ten_color_cases += [tuple(rng.randrange(10) for _ in range(10)) for _ in range(10000)]
    for hats in ten_color_cases:
        inspect_world(hats)
    # Each local binary protocol is a two-entry table indexed by the OTHER hat.
    winning = protocols = 0
    for first, second in product(tuple(product((0, 1), repeat=2)), repeat=2):
        counts = [int(first[b] == a) + int(second[a] == b) for a, b in product((0, 1), repeat=2)]
        assert sum(counts) == 4  # Each player correct in two of the four worlds.
        if min(counts) >= 1:
            assert counts == [1, 1, 1, 1]  # No universally winning protocol allows both correct.
            winning += 1
        protocols += 1
    assert winning == 2 and protocols == 16
    rejected = 0
    for args in ((0, [], 0), (2, [0], 2), (0, [], 2), (0, [2], 2), (True, [0], 2), (0, [True], 2)):
        try:
            model.guess_from_others(*args)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(args)
    return {"question_id": "PREP-127", "status": "passed", "exhaustive_worlds_n1_to_n5": worlds,
            "ten_color_worlds": len(ten_color_cases), "binary_local_protocol_pairs": protocols,
            "universally_winning_binary_protocols": winning, "invalid_cases_rejected": rejected,
            "scope": "Actual local-observation controller, all small worlds/all binary local protocols and seeded ten-color worlds. The written modular/counting proof covers all 10^10 assignments; they were not enumerated."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-127-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
