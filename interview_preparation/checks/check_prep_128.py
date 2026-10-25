"""Independent history-suffix and distinguishing-continuation checks."""
import importlib.util
import itertools
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pattern128", BANK / "solutions/prep_128_sequence_01011.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
PATTERN = (0, 1, 0, 1, 1)


def run_checks():
    words = prefixes = streams = control_edges = 0
    for length in range(13):
        for word in itertools.product((0, 1), repeat=length):
            state = mealy = 0
            for end, bit in enumerate(word, 1):
                state = model.moore_step(state, bit)
                mealy, event = model.mealy_event(mealy, bit)
                history = word[:end]
                expected = int(history[-5:] == PATTERN)
                assert model.moore_output(state) == event == expected
                suffix_lengths = [k for k in range(1, 6) if history[-k:] == PATTERN[:k]]
                assert state == max(suffix_lengths, default=0)
                prefixes += 1
            words += 1
    for controls in itertools.product(itertools.product((0, 1), repeat=2), repeat=6):
        state, history = 0, []
        for bit, reset in controls:
            state = model.moore_step(state, bit, reset)
            history = [] if reset else history + [bit]
            assert model.moore_output(state) == int(tuple(history[-5:]) == PATTERN)
            control_edges += 1
        streams += 1
    moore_pairs = mealy_pairs = 0
    for i, j in itertools.combinations(range(6), 2):
        if j == 5:
            assert model.moore_output(i) != model.moore_output(j)
        else:
            left, right = i, j
            for bit in PATTERN[j:]:
                left, right = model.moore_step(left, bit), model.moore_step(right, bit)
            assert model.moore_output(left) != model.moore_output(right)
        moore_pairs += 1
    for i, j in itertools.combinations(range(5), 2):
        left, right = i, j
        for bit in PATTERN[j:]:
            left, a = model.mealy_event(left, bit)
            right, b = model.mealy_event(right, bit)
        assert a != b
        mealy_pairs += 1
    for target in range(6):
        state = 0
        for bit in PATTERN[:target]:
            state = model.moore_step(state, bit)
        assert state == target
    assert not any(PATTERN[:k] == PATTERN[-k:] for k in range(1, 5))
    assert model.moore_step(4, 0) == 3
    return {"question_id": "PREP-128", "status": "passed", "exhaustive_words": words,
            "prefix_checks": prefixes, "reset_data_streams": streams, "reset_data_edges": control_edges,
            "moore_distinguished_pairs": moore_pairs, "mealy_distinguished_pairs": mealy_pairs,
            "scope": "Executed finite Python state models versus independent literal history suffixes; reachable-state and distinguishing-suffix proofs under the specified clock/output contract. No HDL, synthesis or physical timing; human review pending."}


if __name__ == "__main__":
    evidence = run_checks()
    (BANK / "checks/prep-128-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))
