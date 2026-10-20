"""Independent bounded physical-walk oracle plus complete table/fault checks."""
import importlib.util
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("doorway_model", BANK / "solutions/prep_053_doorway_counter.py")
model = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = model
spec.loader.exec_module(model)
C = model.DoorwayCounter


def run():
    samples = 0
    # Position on a line, 4 sample positions per doorway crossing.
    # Derive observations geometrically rather than using the FSM transition table.
    sensor = (0b00, 0b10, 0b11, 0b01)

    def walk(depth, position, last_boundary, counter):
        nonlocal samples
        if not depth:
            return
        for movement in (-1, 0, 1):
            new_position = position + movement
            ab = sensor[new_position % 4]
            expected = 0
            boundary = last_boundary
            if new_position % 4 == 0:
                expected = (new_position - last_boundary) // 4
                boundary = new_position
            clone = C(counter.count, counter.maximum, counter.state, counter.count_valid)
            got = clone.sample(ab >> 1, ab & 1)
            assert got == expected, (position, new_position, counter, got, expected)
            assert clone.count == 4 + boundary // 4
            assert clone.count_valid
            samples += 1
            walk(depth - 1, new_position, boundary, clone)

    walk(10, 0, 0, C(count=4, maximum=8))

    # Every state/input, with invalid inputs derived from the local path geometry.
    rows = {
        "IDLE": {0: "IDLE", 1: "X1", 2: "E1"},
        "E1": {0: "IDLE", 2: "E1", 3: "E2"},
        "E2": {2: "E1", 3: "E2", 1: "E3"},
        "E3": {3: "E2", 1: "E3", 0: "IDLE"},
        "X1": {0: "IDLE", 1: "X1", 3: "X2"},
        "X2": {1: "X1", 3: "X2", 2: "X3"},
        "X3": {3: "X2", 2: "X3", 0: "IDLE"},
        "WAIT_CLEAR": {0: "IDLE", 1: "WAIT_CLEAR", 2: "WAIT_CLEAR", 3: "WAIT_CLEAR"},
    }
    for state, valid in rows.items():
        for ab in range(4):
            counter = C(4, 8, state, state != "WAIT_CLEAR")
            counter.sample(ab >> 1, ab & 1)
            assert counter.state == valid.get(ab, "WAIT_CLEAR")
            assert counter.count_valid == (state != "WAIT_CLEAR" and ab in valid)

    counter = C(4, 8)
    for ab in (2, 1, 0):  # 10 -> 01 skips overlap: reject and resynchronize.
        assert counter.sample(ab >> 1, ab & 1) == 0
    assert counter.state == "IDLE" and counter.count == 4 and not counter.count_valid
    for ab in (2, 3, 1, 0):
        counter.sample(ab >> 1, ab & 1)
    assert counter.count == 5 and not counter.count_valid  # Sticky until trusted reset.

    for initial, path in ((0, (1, 3, 2, 0)), (8, (2, 3, 1, 0))):
        counter = C(initial, 8)
        for ab in path:
            counter.sample(ab >> 1, ab & 1)
        assert counter.count == initial and not counter.count_valid
    for invalid in (-1, 2, None):
        try:
            C().sample(invalid, 0)
        except ValueError:
            pass
        else:
            raise AssertionError("Nonbinary sensor accepted")
    result = {
        "question_id": "PREP-053", "status": "passed",
        "physical_walk_depth": 10, "physical_oracle_samples": samples,
        "complete_state_input_pairs": 32,
        "covered": ["entry", "exit", "pause", "all bounded reversals", "retreat without counting",
                    "skipped transition", "wait for clear", "sticky invalid count", "underflow", "overflow", "binary validation"],
        "limits": "Python finite-state model and bounded independent geometric walks; not HDL compilation, synthesis, CDC analysis or physical sensor testing. Correctness relies on one passage, observed overlap and known initial occupancy.",
    }
    (BANK / "checks/prep-053-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
