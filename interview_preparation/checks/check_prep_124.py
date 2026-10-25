"""Nonuniform spatial-front simulations against burn-time-coordinate oracles."""

import importlib.util
import json
import random
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rope_model", BANK / "solutions/prep_124_nonuniform_rope_clock.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def compositions(total, parts):
    if parts == 1:
        yield (total,)
    else:
        for first in range(1, total - parts + 2):
            for rest in compositions(total - first, parts - 1):
                yield (first,) + rest


def burn_coordinate(profile, position):
    # Integrate piecewise density over physical [0, position]; independent of
    # the event solver's next-boundary mechanics and speed calculations.
    return sum(Fraction(duration) * max(Fraction(0), min(Fraction(1), position - index))
               for index, duration in enumerate(profile))


def verify_profiles(a, b):
    count = 0
    for start in ("left", "right"):
        result = model.measure_three_quarters(a, b, b_start=start)
        assert result["first_burnout_minutes"] == sum(a) / 2 == 30
        assert result["final_burnout_minutes"] == (sum(b) + 30) / 2 == 45
        assert burn_coordinate(a, result["meeting_a"]) == 30
        # The initially lit front runs 45 minutes, the delayed front 15.
        assert burn_coordinate(b, result["meeting_b"]) == (45 if start == "left" else 15)
        count += 1
    reversed_a = model.burnout(tuple(reversed(a)), left=0, right=0)
    original_a = model.burnout(a, left=0, right=0)
    assert reversed_a[0] == original_a[0] and reversed_a[1] + original_a[1] == len(a)
    return count


def run_checks():
    profiles = [tuple(Fraction(value * 10) for value in parts)
                for length in range(1, 5) for parts in compositions(6, length)]
    exhaustive = sum(verify_profiles(a, b) for a in profiles for b in profiles)
    rng = random.Random(124)
    random_cases = 0
    for _ in range(400):
        pair = []
        for _rope in range(2):
            weights = [rng.randrange(1, 101) for _ in range(rng.randrange(2, 13))]
            pair.append(tuple(Fraction(60 * weight, sum(weights)) for weight in weights))
        random_cases += verify_profiles(*pair)
    illustrated = model.measure_three_quarters((5, 10, 15, 30), (40, 10, 5, 5))
    assert illustrated["meeting_a"] == 3  # Three quarters of physical length, not half.
    assert illustrated["meeting_b"] == Fraction(3, 2)  # Out of four equal spatial segments.
    for profile in ((60,), (1, 59), (59, 1), (1, 1, 1, 57)):
        assert model.burnout(profile, left=0, right=None)[0] == 60
        assert model.burnout(profile, left=None, right=0)[0] == 60
    rejected = 0
    for call in (lambda: model.burnout(()), lambda: model.burnout((0, 60)),
                 lambda: model.burnout((-1, 61)), lambda: model.burnout((60,), left=None),
                 lambda: model.burnout((60,), left=-1),
                 lambda: model.measure_three_quarters((59,), (60,)),
                 lambda: model.measure_three_quarters((60,), (60,), b_start="middle")):
        try:
            call()
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("invalid model input was accepted")
    return {"question_id": "PREP-124", "status": "passed", "first_event_minutes": 30,
            "final_event_minutes": 45, "exhaustive_profiles": len(profiles),
            "exhaustive_profile_pair_directions": exhaustive,
            "seeded_profile_pair_directions": random_cases, "invalid_cases_rejected": rejected,
            "scope": "Exact spatial piecewise flame-front simulations with unrelated nonuniform profiles, both start orientations and independent cumulative burn-time oracles. No physical experiment or universal claim about arbitrary flame physics."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-124-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
