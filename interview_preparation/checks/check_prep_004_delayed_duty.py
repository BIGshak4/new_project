"""Independent index oracle and exact rational sampled-duty checks."""
import importlib.util
import itertools
import json
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("delayed", BANK / "solutions/prep_004_delayed_edges_duty.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def verify():
    words = 0
    for length in range(13):
        for word in itertools.product((0, 1), repeat=length):
            for initial in (0, 1):
                history = [initial, initial] + list(word)
                expected = [int(history[k + 1] != history[k]) for k in range(length)]
                assert model.delayed_edges(word, initial) == expected
                words += 1
    assert model.delayed_edges([0, 1, 1]) == [0, 0, 1]
    for period in range(2, 202, 2):
        ones, total = model.steady_duty(period)
        assert Fraction(ones, total) == Fraction(2, period)
    # Analog 50%-duty square wave sampled at the same frequency can look constant.
    aliased = [int((Fraction(k) + Fraction(1, 4)) % 1 >= Fraction(1, 2)) for k in range(50)]
    assert len(set(aliased)) == 1 and sum(model.delayed_edges(aliased)) == 0
    assert model.steady_duty(2) == (2, 2)
    return {"status": "passed", "binary_stream_initializations": words,
            "even_sampled_periods": 100, "alignment_example": "011 -> 001",
            "alias_counterexample": "50% analog input may yield constant sampled input",
            "scope": "Python sampled-state and exact-rational model; no HDL, STA or CDC validation"}


if __name__ == "__main__":
    result = verify()
    (BANK / "checks/prep-004-delayed-duty-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
