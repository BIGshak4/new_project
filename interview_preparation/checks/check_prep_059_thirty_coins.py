"""Enumerate every placement of three black faces among thirty coins."""
import importlib.util
import json
from itertools import combinations
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("coins059variant", BANK / "solutions/prep_059_thirty_coins_three_black.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    selected, rest, flips = model.blind_plan()
    assert set(selected).isdisjoint(rest) and set(selected) | set(rest) == set(range(30))
    assert len(selected) == 3 and len(rest) == 27 and flips == selected
    cases = 0
    seen = set()
    for black_positions in combinations(range(30), 3):
        faces = [int(i in black_positions) for i in range(30)]
        before = sum(faces[i] for i in selected)
        for i in flips:
            faces[i] ^= 1
        a, b = sum(faces[i] for i in selected), sum(faces[i] for i in rest)
        assert a == b == 3 - before
        seen.add((before, a))
        cases += 1
    assert seen == {(0, 3), (1, 2), (2, 1), (3, 0)}
    return {"question_id": "PREP-059", "variant": "thirty_coins_three_black", "status": "passed",
            "all_three_black_placements": cases, "distinct_selected_black_counts": len(seen),
            "blind_plan_receives_orientation_information": False,
            "scope": "Every one of C(30,3)=4060 initial arrangements tested. The planner sees only total and known black count; the verifier alone sees orientations."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-059-thirty-coins-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
