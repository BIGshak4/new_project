"""Independent complete bounded checks for the 25-Oct hardware intake."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(folder, name):
    spec = importlib.util.spec_from_file_location(name, BANK / folder / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("number", (128, 130, 134))
def test_independent_history_or_arithmetic_checks_match_saved_evidence(number):
    result = load("checks", f"check_prep_{number}").run_checks()
    assert result == json.loads((BANK / "checks" / f"prep-{number}-verification.json").read_text())
    assert result["status"] == "passed"


def test_pattern_partial_fallback_and_post_edge_match_pulse():
    model = load("solutions", "prep_128_sequence_01011")
    state, seen = 0, []
    for bit in (0, 1, 0, 1, 0, 1, 1):
        state = model.moore_step(state, bit)
        seen.append(model.moore_output(state))
    assert seen == [0, 0, 0, 0, 0, 0, 1]
    assert model.moore_step(5, 0, reset=1) == 0
    assert model.moore_step(4, 0) == 3


def test_unsigned_boundary_and_width_contracts():
    clamp = load("solutions", "prep_130_eight_bit_lower_clamp")
    assert [clamp.clamp_lower64(x) for x in (0, 63, 64, 65, 127, 128, 255)] == [64, 64, 64, 65, 127, 128, 255]
    multiplier = load("solutions", "prep_134_constant_times_thirteen")
    assert multiplier.times_thirteen(255, 8) == 3315
    assert multiplier.times_thirteen(1, 1) == 13
    with pytest.raises(ValueError):
        multiplier.times_thirteen(256, 8)
