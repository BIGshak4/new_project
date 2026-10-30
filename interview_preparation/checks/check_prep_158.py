"""Compare tick iteration with an independent integer-divisibility oracle."""
import importlib.util
import json
from fractions import Fraction
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pointers158", BANK / "solutions/prep_158_synchronous_array_pointers.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    cases = 0
    for size in range(1, 16):
        for left, right, ls, rs in product(range(1, size + 1), range(1, size + 1), (1, 2, 4), (1, 3, 5)):
            difference, step_sum = right - left, ls + rs
            t = difference // step_sum
            position = left + ls * t
            expected = (t, position) if difference >= 0 and difference % step_sum == 0 and 1 <= position <= size else None
            assert model.simultaneous_meeting(size=size, left_start=left, right_start=right,
                                              left_step=ls, right_step=rs) == expected
            cases += 1
    source = list(model.visits())
    assert model.simultaneous_meeting() is None
    assert source[19] == (19, 40, 41) and source[20] == (20, 42, 38)
    assert model.continuous_intersection() == (Fraction(96, 5), Fraction(202, 5))
    left_values = {left for _, left, _ in source}
    right_values = {right for _, _, right in source}
    assert 38 in left_values & right_values  # Same cell at different ticks is not a meeting.
    return {"question_id": "PREP-158", "status": "passed", "integer_configuration_cases": cases,
            "source_simultaneous_meetings": 0, "first_reversed_order_tick": 20,
            "continuous_intersection_time": "96/5", "continuous_intersection_position": "202/5",
            "scope": "Discrete integer visits and separately specified exact linear interpolation; no implied continuous pointer motion."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-158-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
