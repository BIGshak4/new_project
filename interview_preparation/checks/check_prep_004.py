"""Check the sampled change detector's logical behavior, not physical timing."""

import json
from itertools import product
from pathlib import Path


def check(samples, initial=0, resets=None):
    q1 = q2 = previous = initial
    registered_out = 0
    reference_previous = initial
    observed = []
    if resets is None:
        resets = [False] * len(samples)
    for sample, reset in zip(samples, resets):
        if reset:
            q1 = q2 = previous = registered_out = reference_previous = 0
            expected = 0
        else:
            expected = int(sample != reference_previous)
            reference_previous = sample
            q1, q2 = sample, q1
            previous, registered_out = sample, sample ^ previous
        actual = q1 ^ q2
        assert actual == registered_out == expected
        observed.append(actual)
    return observed


bank = json.loads((Path(__file__).resolve().parents[1] / "questions.json").read_text(encoding="utf-8"))
question = next(q for q in bank["questions"] if q["id"] == "PREP-004")
waveform = question["waveform_observations"]
assert check(waveform["input_at_rising_edge"]) == waveform["output_after_rising_edge"]
for initial in (0, 1):
    for samples in product((0, 1), repeat=8):
        check(samples, initial)
assert check([0, 1, 1, 0, 1], resets=[False, False, True, False, False]) == [0, 1, 0, 0, 1]
print("PASS: source waveform, 512 length-8 sequences, and synchronous reset; both implementations agree.")
print("Scope: discrete logic only; no HDL simulation, metastability or gate-delay analysis.")
