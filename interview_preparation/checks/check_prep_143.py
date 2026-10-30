"""Exact mixture and independent arbitrary-spoon conservation checks."""
import importlib.util
import json
from fractions import Fraction
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cups_model", BANK / "solutions/prep_143_two_cup_transfer.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    mixed = equal = arbitrary = 0
    for a, b in product(range(1, 13), repeat=2):
        for s in range(a + 1):
            actual = model.mixed_transfer(a, b, s)
            # Independently subtract the returned mixture vector from cup B.
            red_b = Fraction(s)
            blue_b = Fraction(b)
            fraction_removed = Fraction(s, b + s)
            red_removed = red_b * fraction_removed
            blue_removed = blue_b * fraction_removed
            expected_b = (red_b - red_removed, blue_b - blue_removed)
            assert (actual["red_in_blue_cup"], actual["blue_in_blue_cup"]) == expected_b
            assert actual["red_in_red_cup"] + actual["red_in_blue_cup"] == a
            assert actual["blue_in_red_cup"] + actual["blue_in_blue_cup"] == b
            assert actual["red_in_red_cup"] + actual["blue_in_red_cup"] == a
            assert actual["red_in_blue_cup"] + actual["blue_in_blue_cup"] == b
            assert actual["blue_in_red_cup"] == actual["red_in_blue_cup"]
            if a == b:
                assert actual["foreign_fraction_red_cup"] == actual["foreign_fraction_blue_cup"]
                equal += 1
            elif s:
                assert ((actual["foreign_fraction_red_cup"] < actual["foreign_fraction_blue_cup"])
                        == (a > b))
            mixed += 1
            for r in range(max(0, s - b), s + 1):
                result = model.return_any_composition(a, b, s, r)
                assert result["blue_in_red_cup"] == result["red_in_blue_cup"] == s - r
                arbitrary += 1
    rejected = 0
    for call in (lambda: model.mixed_transfer(0, 1, 0), lambda: model.mixed_transfer(1, 0, 0),
                 lambda: model.mixed_transfer(1, 1, -1), lambda: model.mixed_transfer(1, 1, 2),
                 lambda: model.return_any_composition(1, 1, 1, 2)):
        try:
            call()
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("invalid transfer accepted")
    unequal = model.mixed_transfer(100, 50, 10)
    assert unequal["foreign_fraction_red_cup"] == Fraction(1, 12)
    assert unequal["foreign_fraction_blue_cup"] == Fraction(1, 6)
    return {"question_id": "PREP-143", "status": "passed", "mixed_exact_cases": mixed,
            "equal_initial_volume_cases": equal, "arbitrary_return_composition_cases": arbitrary,
            "invalid_cases_rejected": rejected,
            "scope": "Exact rational liquid volumes and homogeneous-mixture illustration; no optical or perceived-color model."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-143-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
