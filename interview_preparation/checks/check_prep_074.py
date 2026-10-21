"""Exhaustive finite sequence and illustrative delay checks for PREP-074."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_074_xor_feedback_dff import delayed_events, feedback_timing_ok, next_q, trace


def main():
    rows = 0
    for q, a in itertools.product(range(2), repeat=2):
        assert next_q(q, a) == (q if a == 0 else 1 - q)
        rows += 1
    streams = edges = 0
    for n in range(11):
        for data in itertools.product(range(2), repeat=n):
            for q0 in range(2):
                states = trace(q0, list(data))
                for k, q in enumerate(states):
                    assert q == ((q0 + sum(data[:k])) % 2)
                streams += 1
                edges += n
    events = delayed_events(0, [1] * 8, 10, 1.25)
    assert events == [(11.25 + 10 * i, 1 - i % 2) for i in range(8)]
    assert all(events[i + 2][0] - events[i][0] == 20 for i in range(6))
    assert delayed_events(0, [0] * 8, 10, 1.25) == []
    assert delayed_events(1, [0] * 8, 10, 1.25) == []
    assert feedback_timing_ok(10, 2, 3, 1, 0.5, 0.25, 0.5)
    assert not feedback_timing_ok(5, 2, 3, 1, 0.5, 0.25, 0.5)
    assert not feedback_timing_ok(10, 2, 3, 1, 0.1, 0.1, 0.5)
    evidence = {"question_id": "PREP-074", "status": "passed", "truth_rows": rows,
                "exhaustive_streams": streams, "sampling_edges": edges,
                "maximum_input_length": 10, "delayed_toggle_events": len(events),
                "scope": "Python Boolean model and constant-delay illustration; no HDL, analogue, STA or physical verification",
                "professional_review": "pending"}
    (BANK / "checks/prep-074-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
