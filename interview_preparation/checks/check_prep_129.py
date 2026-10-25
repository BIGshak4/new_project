"""Event trace checked against an independent global-time piecewise path."""

import importlib.util
import json
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("snail_model", BANK / "solutions/prep_129_snail_alternating_minutes.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def grid_first_contact(height, up, down):
    # With these integral rates and target heights the true contact lies on a
    # 1/12-minute grid. This oracle describes height from global time, never
    # updating position using the event model's loop.
    for tick in range(24 * (height + 1) + 1):
        time = Fraction(tick, 12)
        cycles, phase = divmod(time, 2)
        position = cycles * (up - down)
        position += up * phase if phase <= 1 else up - down * (phase - 1)
        if position >= height:
            return time
    raise AssertionError("positive-drift path did not reach target")


def run_checks():
    finish, trace = model.first_contact()
    assert finish == 17
    assert sum(step[0] in ("climb", "final_climb") for step in trace) == 9
    assert sum(step[0] == "rest_slide" for step in trace) == 8
    assert trace[-1] == ("final_climb", 16, 17, 8, 10)
    cases = 0
    for up in range(1, 5):
        for down in range(up):
            for height in range(1, 31):
                actual, events = model.first_contact(height, up, down)
                assert actual == grid_first_contact(height, up, down)
                assert events[-1][0] == "final_climb" and events[-1][-1] == height
                assert all(event[-1] < height for event in events[:-1])
                cases += 1
    fractions = 0
    for height in (Fraction(1, 2), Fraction(7, 2), Fraction(19, 2)):
        actual, _ = model.first_contact(height)
        cycles = max(0, -(-(height - 2) // 1))
        assert actual == cycles * 2 + (height - cycles) / 2
        fractions += 1
    assert model.first_contact(0) == (0, [])
    assert model.first_contact(2, 1, 1) == (None, [])
    assert model.first_contact(Fraction(1, 2), 1, 2)[0] == Fraction(1, 2)
    rejected = 0
    for args in ((-1,), (1, 0), (1, 1, -1), (1, 1, 1, 0), (1, 1, 1, 1, -1)):
        try:
            model.first_contact(*args)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(args)
    return {"question_id": "PREP-129", "status": "passed", "first_contact_minutes": 17,
            "climbs": 9, "completed_rests": 8, "independent_global_time_grid_cases": cases,
            "fractional_height_cases": fractions, "invalid_cases_rejected": rejected,
            "scope": "Exact piecewise-linear first-contact model against an independent global-time height oracle. No physical snail experiment or different daily schedule is claimed."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-129-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
