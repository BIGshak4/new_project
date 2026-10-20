"""Exhaustive Python-model and state-distinguishability checks, not HDL simulation."""
from __future__ import annotations

import importlib.util
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prep050", ROOT / "solutions/prep_050_lsb_divisible_by_five.py")
model = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = model
spec.loader.exec_module(model)


def main() -> None:
    words = prefix_steps = 0
    for length in range(17):
        for word in itertools.product((0, 1), repeat=length):
            detector = model.DivisibleByFiveLSB()
            value = 0
            assert detector.divisible
            for position, bit in enumerate(word):
                value += bit << position
                actual = detector.tick(bit)
                assert actual == (value % 5 == 0)
                assert detector.state == (pow(2, -(position + 1), 5) * value) % 5
                prefix_steps += 1
            words += 1
    control_traces = control_steps = 0
    # 0=hold, 1=accept zero, 2=accept one, 3=reset (also with valid high).
    for actions in itertools.product(range(4), repeat=7):
        detector = model.DivisibleByFiveLSB()
        value, position = 0, 0
        for action in actions:
            if action == 3:
                value, position = 0, 0
                actual = detector.tick(1, valid=True, reset=True)
            elif action == 0:
                actual = detector.tick(1, valid=False)
            else:
                bit = action - 1
                value += bit << position
                position += 1
                actual = detector.tick(bit)
            assert actual == (value % 5 == 0)
            assert detector.state == (value * pow(2, -position, 5)) % 5
            control_steps += 1
        control_traces += 1
    transitions = 0
    for state in range(5):
        for bit in (0, 1):
            assert model.advance(state, bit) == (3 * (state + bit)) % 5
            transitions += 1
    reachable = {0}
    for _ in range(3):
        reachable |= {model.advance(s, b) for s in reachable for b in (0, 1)}
    assert reachable == set(range(5))
    distinguished = 0
    for first, second in itertools.combinations(range(5), 2):
        # The suffix value v=-first mod 5 fits in three LSB-first bits.
        suffix_value = (-first) % 5
        a, b = first, second
        for position in range(3):
            bit = (suffix_value >> position) & 1
            a, b = model.advance(a, bit), model.advance(b, bit)
        assert a == 0 and b != 0
        distinguished += 1
    assert model.divisible_lsb([1, 0, 0, 1, 1])  # 25, counterexample to MSB recurrence
    assert not model.divisible_lsb([1, 1, 0, 0, 1])  # 19
    report = {
        "question_id": "PREP-050", "status": "passed", "checked_on": "2026-10-20",
        "all_words_lengths_0_through_16": words, "checked_prefix_steps": prefix_steps,
        "length_7_control_traces": control_traces, "checked_control_steps": control_steps,
        "state_input_transitions": transitions, "reachable_states": len(reachable),
        "distinguished_state_pairs": distinguished,
        "oracle": "Independent exact integer sum of bits times powers of two; normalized state invariant also asserted.",
        "limitations": "Python functional models only. SystemVerilog not compiled/simulated; no synthesis, hardware timing or expert approval.",
    }
    (ROOT / "checks/prep-050-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
