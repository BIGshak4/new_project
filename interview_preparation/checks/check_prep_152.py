"""All 32 state transitions, repeated wraps and aligned reset checks."""

import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "counter152", BANK / "solutions/prep_152_extend_mod16_counter.py"
)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    def blackbox(low, reset):
        # Independent transition lookup for the supplied opaque component.
        table = tuple(range(1, 16)) + (0,)
        return 0 if reset else table[low]

    transitions = resets = trace_steps = 0
    for state in range(32):
        counter = model.ExtendedCounter(blackbox, state & 15, state >> 4)
        assert counter.edge() == (state + 1) % 32
        transitions += 1
        assert counter.edge(reset=True) == 0
        resets += 1
        counter = model.ExtendedCounter(blackbox, state & 15, state >> 4)
        for cycle in range(1, 98):
            assert counter.edge() == (state + cycle) % 32
            trace_steps += 1
    rejected = 0
    for low, high in ((-1, 0), (16, 0), (True, 0), (0, 2), (0, True)):
        try:
            model.next_high(low, high)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError((low, high))
    assert model.next_high(15, 0) == 1 and model.next_high(15, 1) == 0
    return {
        "question_id": "PREP-152",
        "status": "passed",
        "all_state_transitions": transitions,
        "aligned_reset_cases": resets,
        "long_trace_edges": trace_steps,
        "invalid_states_rejected": rejected,
        "scope": "Executed logical same-clock Python model with independent modulo-16 transition lookup and modulo-32 oracle. Old low=15 triggers high toggle. No black-box internals, HDL, generated-clock or physical timing validation.",
    }


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-152-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))
