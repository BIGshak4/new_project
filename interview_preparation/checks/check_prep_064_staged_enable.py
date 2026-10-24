"""Exhaust gate equations against arithmetic and the existing inc/dec model."""

import importlib.util
import json
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("staged_counter", BANK / "solutions/prep_064_staged_enable.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
original_spec = importlib.util.spec_from_file_location("original_counter", BANK / "solutions/prep_064_three_bit_up_down.py")
original = importlib.util.module_from_spec(original_spec)
original_spec.loader.exec_module(original)


def run_checks():
    transitions = streams = reset_cases = rejected = specializations = 0
    for width, direction in product((1, 3), ("up", "down")):
        modulus = 2**width
        step = 1 if direction == "up" else -1
        for state, enable in product(range(modulus), (0, 1)):
            assert model.next_state(state, enable, width=width, direction=direction) == (state + step * enable) % modulus
            assert model.next_state(state, enable, width=width, direction=direction, reset=1) == 0
            transitions += 1
            reset_cases += 1
            if width == 3:
                inc, dec = (enable, 0) if direction == "up" else (0, enable)
                assert model.next_state(state, enable, direction=direction) == original.next_q(state, inc, dec)
                assert original.next_q(state, 1, 1) == state
                specializations += 1
        for start in range(modulus):
            for inputs in product((0, 1), repeat=8):
                state = start
                for enable in inputs:
                    state = model.next_state(state, enable, width=width, direction=direction)
                # Independent count of requests; no gate recurrence in this oracle.
                assert state == (start + step * sum(inputs)) % modulus
                streams += 1
    # The source's one-bit up/down behaviors coincide modulo two.
    for state, enable in product((0, 1), repeat=2):
        assert model.next_state(state, enable, width=1, direction="up") == model.next_state(state, enable, width=1, direction="down")
    for args, kwargs in [((8, 1), {}), ((-1, 0), {}), ((True, 1), {}),
                         ((0, True), {}), ((0, 2), {}), ((0, 0), {"width": 2}),
                         ((0, 0), {"direction": "sideways"}), ((0, 0), {"reset": 2})]:
        try:
            model.next_state(*args, **kwargs)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError((args, kwargs))
    return {"question_id": "PREP-064", "variant": "batch30_staged_enable", "status": "passed",
            "state_enable_direction_cases": transitions, "reset_priority_cases": reset_cases,
            "eight_cycle_enable_streams": streams, "invalid_cases_rejected": rejected,
            "original_control_specializations": specializations,
            "scope": "Exhaustive finite Boolean gate model against independent arithmetic and request counts; no HDL compilation or physical timing simulation."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-064-staged-enable-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
