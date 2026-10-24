"""Independent arithmetic, state and timing checks for PREP-100/103/104.

Python models are executed here; the figures and explanations do not imply HDL
compilation, analog metastability simulation or proof of physical timing.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
from collections import deque
from fractions import Fraction
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MULTIPLIER = load("prep_100_times_six_full_adders")
CONVERSION = load("prep_103_dff_from_tff")
TIMING = load("prep_104_pipeline_timing")


def test_all_byte_inputs_and_actual_eight_full_adder_column_wiring():
    for value in range(256):
        result, columns = MULTIPLIER.times_six(value, with_trace=True)
        assert result == sum([value] * 6)
        assert len(columns) == 8
        assert [row["column"] for row in columns] == list(range(2, 10))
        assert result < 2**11 and result % 2 == 0
        for row in columns:
            column = row["column"]
            left_copy_bit = ((value * 2) // (2**column)) % 2
            right_copy_bit = ((value * 4) // (2**column)) % 2
            assert (row["a"], row["b"]) == (left_copy_bit, right_copy_bit)
            assert row["sum"] + 2 * row["carry_out"] == sum(
                (row["a"], row["b"], row["carry_in"]))
    assert MULTIPLIER.times_six(255) == 1530 >= 2**10
    for invalid in (-1, 256, True, None, 1.5):
        with pytest.raises(ValueError):
            MULTIPLIER.times_six(invalid)


def test_tff_conversion_matches_direct_data_capture_from_both_binary_initial_states():
    for initial in (0, 1):
        for length in range(11):
            for samples in itertools.product((0, 1), repeat=length):
                assert CONVERSION.trace(samples, initial=initial) == list(samples)
    for q, data in itertools.product((0, 1), repeat=2):
        assert CONVERSION.dff_from_tff(q, data, rising_edge=False) == q
    for q, toggle in itertools.product((0, 1), repeat=2):
        assert CONVERSION.tff(q, toggle) == (1 - q if toggle else q)
    with pytest.raises(ValueError):
        CONVERSION.dff_from_tff(0, 2)
    with pytest.raises(ValueError):
        CONVERSION.dff_from_tff(True, 0)


def test_three_stage_model_against_independent_queue_for_all_short_streams():
    for initial in itertools.product((0, 1), repeat=3):
        for length in range(9):
            for samples in itertools.product((0, 1), repeat=length):
                expected = deque(initial[::-1])
                for sample, state in zip(samples, TIMING.pipeline(samples, initial=initial), strict=True):
                    expected.popleft()
                    expected.append(sample)
                    assert state == tuple(expected)[::-1]
    assert TIMING.pipeline([1, 1, 1]) == [(1, 0, 0), (1, 1, 0), (1, 1, 1)]
    assert TIMING.pipeline([0, 1, 1, 1])[-2:] == [(1, 1, 0), (1, 1, 1)]


def test_signed_skew_has_opposite_effects_and_period_does_not_change_hold():
    base = dict(period=Fraction(4), cq_max=Fraction(1), logic_max=Fraction(2),
                setup=Fraction(1), cq_min=Fraction(1, 4), logic_min=Fraction(1, 4), hold=Fraction(1, 2))
    at_limit = TIMING.timing_slacks(**base)
    assert at_limit == {"setup": 0, "hold": 0}
    for skew in (Fraction(-1, 2), Fraction(0), Fraction(1, 2)):
        result = TIMING.timing_slacks(**base, skew=skew)
        assert result == {"setup": skew, "hold": -skew}
        slower = TIMING.timing_slacks(**(base | {"period": 5}), skew=skew)
        assert slower["hold"] == result["hold"]
        assert slower["setup"] == result["setup"] + 1
    for bad in (base | {"period": 0}, base | {"cq_min": 2}, base | {"logic_min": -1}):
        with pytest.raises(ValueError):
            TIMING.timing_slacks(**bad)


def test_archived_models_and_reproducible_evidence_remain_honestly_scoped():
    expected = {
        100: ("exhaustive_unsigned_inputs", 256),
        103: ("exhaustive_streams", 4094),
        104: ("exact_rational_timing_cases", 216),
    }
    for number, (field, count) in expected.items():
        evidence = json.loads((BANK / "checks" / f"prep-{number:03d}-verification.json").read_text())
        assert evidence["status"] == "passed" and evidence[field] == count
        assert "No" in evidence["scope"] or "no" in evidence["scope"]
    document = (BANK / "questions/prep-104-three-stage-pipeline-timing.md").read_text(encoding="utf-8")
    assert "latency alone is not a certain fault diagnosis" in document
    assert "אינה הוכחה" in document
    assert "hold:  tCQ(min) + tCD(min) >= skew + tHold" in document
    assert "setup: tCQ(max) + tPD(max) + tSetup <= T + skew" in document
    for source in (10, 17, 19):
        assert (BANK / "sources" / f"2026-10-24-batch20-{source:02d}.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    for stem in ("prep-100-eight-fa-circuit", "prep-103-tff-feedback-circuit",
                 "prep-104-prompt-pipeline", "prep-104-timing-constraints"):
        for language in ("he", "en"):
            assert (BANK / "diagrams" / f"{stem}-{language}.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
