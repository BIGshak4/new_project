"""Frozen review membership before Nov7 and the single new invalidation.

Learner-copy edits on Nov4 already invalidated 25 earlier matches. Never restore
those flags: reconstruct all 255 old compiled objects through the exact intake
projection, then compare their content with the unchanged attestation registry.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.engine.solution_review import solution_content_hash
from tests.difficulty_history import before_difficulty_review
from tests.preparation_november7_history import baseline, before_batch1107_compiled, digest

BACKEND = Path(__file__).resolve().parents[1]
PRE_INTAKE_REVIEWED_KEYS = frozenset(
[
    "example-array-bound-off-by-one",
    "example-asynchronous-pulse-transfer",
    "example-balanced-brackets",
    "example-bounded-circular-queue",
    "example-count-set-bits",
    "example-credit-dispenser",
    "example-extract-register-field",
    "example-first-greater-or-equal",
    "example-full-adder-composition",
    "example-incomplete-combinational-assignment",
    "example-load-and-serial-shift",
    "example-masked-equality",
    "example-merge-measurement-streams",
    "example-mod-six-counter",
    "example-mux-tree-eight-inputs",
    "example-nand-only-enable",
    "example-nonblocking-pipeline-trace",
    "example-overlapping-sequence-1011",
    "example-pair-sum-indices",
    "example-power-of-two-check",
    "example-request-acknowledge",
    "example-reverse-singly-linked-list",
    "example-rotate-versus-shift",
    "example-sampled-rising-edge",
    "example-sensor-majority",
    "example-setup-hold-calculation",
    "example-signed-overflow",
    "example-unsigned-saturating-adder",
    "prep-binary-tree-vs-bst-maximum",
    "prep-duck-fox-circular-pond-escape",
    "prep-four-hidden-switches-rotating-table",
    "prep-four-input-or-from-threshold-boxes",
    "prep-four-input-sorter-single-crossing-fault",
    "prep-full-adder-32-bit-area-delay-recursive-carry-select",
    "prep-grasshopper-ladder-one-two-steps",
    "prep-hundred-frogs-lamps",
    "prep-hundred-switches-one-observer-question",
    "prep-josephus-forty-three",
    "prep-maximum-of-two-numbers-circuit",
    "prep-moving-rabbit-ten-bushes",
    "prep-multiply-four-registers-unit-instructions",
    "prep-three-people-five-hats-public-reasoning",
    "prep-twelve-coins-three-weighings",
    "prep-wire-wrapped-around-cylinder"
]
)
NOVEMBER7_INVALIDATED_KEYS = frozenset({"prep-multiply-four-registers-unit-instructions"})
NOVEMBER7_BATCH10_INVALIDATED_KEYS = frozenset({"prep-maximum-of-two-numbers-circuit"})


def expected_reviewed_keys():
    registry = json.loads((BACKEND / "seeds/solution_review_attestations.json").read_bytes())
    assert len(registry["questions"]) == 93
    assert digest(registry) == baseline()["review_registry_canonical_sha256"]
    prepared = json.loads((BACKEND / "seeds/questions/preparation_bank.json").read_bytes())
    previous = [before_batch1107_compiled(q) for q in prepared if q["key"] in baseline()["compiled_sha256"]]
    assert len(previous) == len(baseline()["compiled_sha256"]) == 255
    examples = [before_difficulty_review(q) for q in json.loads((BACKEND / "seeds/questions/example_bank.json").read_bytes())]
    assert digest(examples) == "8f3193a297f22cae4257033712858b86ed4e171235b98a628e5ab69cc86cc1ab"
    matched = {q["key"] for q in previous + examples
               if q["key"] in registry["questions"]
               and solution_content_hash(q) == registry["questions"][q["key"]]["content_sha256"]}
    assert matched == PRE_INTAKE_REVIEWED_KEYS and len(matched) == 44
    assert NOVEMBER7_INVALIDATED_KEYS.issubset(matched)
    after_first_intake = matched - NOVEMBER7_INVALIDATED_KEYS
    assert len(after_first_intake) == 43
    assert NOVEMBER7_BATCH10_INVALIDATED_KEYS.issubset(after_first_intake)
    expected = after_first_intake - NOVEMBER7_BATCH10_INVALIDATED_KEYS
    assert len(expected) == 42
    return expected
