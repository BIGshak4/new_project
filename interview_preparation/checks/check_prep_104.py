"""Ideal queue oracle plus exact rational setup/hold margin checks.

Deliberately omitted: a deterministic model of behavior after timing failure.
"""
import itertools
import json
import sys
from collections import deque
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_104_pipeline_timing import pipeline, timing_slacks

streams = edges = 0
for initial in itertools.product((0, 1), repeat=3):
    for length in range(9):
        for samples in itertools.product((0, 1), repeat=length):
            expected = deque(reversed(initial))
            rows = pipeline(samples, initial=initial)
            for sample, state in zip(samples, rows, strict=True):
                expected.popleft()
                expected.append(sample)
                assert tuple(reversed(expected)) == state
            streams += 1
            edges += length
assert pipeline([1, 1, 1, 1]) == [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 1, 1)]
# Two/four-capture traces also have non-timing explanations: wrong stage count
# or an enable that suppresses the first capture. These are counterexamples to
# diagnosis by output latency alone, not predictions of setup/hold failures.
assert [value for value in (0, 1, 1, 1)].index(1) + 1 == 2
assert [state[2] for state in pipeline([0, 1, 1, 1])].index(1) + 1 == 4
checks = 0
for period, skew, cq, logic, setup, hold in itertools.product(
    (Fraction(1), Fraction(2), Fraction(4)),
    (Fraction(-1, 2), Fraction(0), Fraction(1, 2)),
    (Fraction(0), Fraction(1, 2)),
    (Fraction(0), Fraction(1), Fraction(2)),
    (Fraction(0), Fraction(1, 2)),
    (Fraction(0), Fraction(1, 2)),
):
    result = timing_slacks(period=period, skew=skew, cq_max=cq, logic_max=logic,
                           setup=setup, cq_min=cq, logic_min=logic, hold=hold)
    # Absolute launch/capture event times independently express each deadline.
    arrival = cq + logic
    next_capture = period + skew
    same_capture = skew
    assert (result["setup"] >= 0) == (arrival <= next_capture - setup)
    assert (result["hold"] >= 0) == (arrival >= same_capture + hold)
    slower = timing_slacks(period=period + 1, skew=skew, cq_max=cq, logic_max=logic,
                           setup=setup, cq_min=cq, logic_min=logic, hold=hold)
    assert slower["hold"] == result["hold"] and slower["setup"] == result["setup"] + 1
    checks += 1
record = {
    "question_id": "PREP-104", "checked_on": "2026-10-24", "status": "passed",
    "ideal_streams": streams, "ideal_sampling_edges": edges,
    "exact_rational_timing_cases": checks,
    "oracle": "Independent reversed deque for three stages; absolute arrival/capture deadlines for setup and hold. Counterexamples show latency alone is not diagnostic.",
    "scope": "Ideal two-state traces and scalar timing equations with explicit signed skew. No deterministic waveform after violations, analog metastability model, HDL compilation or physical timing certification.",
}
(BANK / "checks/prep-104-verification.json").write_text(
    json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
