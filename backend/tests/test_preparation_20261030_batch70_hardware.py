"""Executed independent checks for LC, run history, logic and added variants."""

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


@pytest.mark.parametrize(
    "suffix",
    ("170", "171", "172", "173", "174", "119_four_seven_70", "115_gate_step_70", "053_single_sensor_70"),
)
def test_independent_models_match_saved_evidence(suffix):
    result = load("checks", f"check_prep_{suffix}").run_checks()
    evidence = BANK / "checks" / f"prep-{suffix.replace('_', '-')}-verification.json"
    assert result == json.loads(evidence.read_bytes())
    assert result["status"] == "passed"


def test_run_error_requires_a_closed_run_and_reset_is_empty():
    model = load("solutions", "prep_171_completed_run_parity")
    assert model.detect((0, 0)) == [0, 0]
    assert model.detect((0, 0, 1)) == [0, 0, 1]
    assert model.detect((1, 0)) == [0, 1]
    assert model.step("OO", 0, reset=True) == (model.RESET_STATE, 0)
    assert model.step(model.RESET_STATE, 0) == ("ZO", 0)
    assert model.step(model.RESET_STATE, 1) == ("OO", 0)


def test_overlap_keeps_the_completed_match_final_one():
    model = load("solutions", "prep_173_overlapping_1011")
    assert model.detections((1, 0, 1, 1, 0, 1, 1)) == [0, 0, 0, 1, 0, 0, 1]
    assert model.step(3, 1) == (1, 1)
    assert model.step(3, 1, reset=True) == (0, 0)


def test_lc_initial_conditions_and_passive_current_direction():
    model = load("solutions", "prep_170_switched_ideal_lc")
    voltage, current = model.response(0.0, 2.0, 0.5, 3.0)
    assert (voltage, current) == (3.0, 0.0)
    next_voltage, next_current = model.response(0.001, 2.0, 0.5, 3.0)
    assert 0 < next_voltage < voltage
    assert next_current > 0
    with pytest.raises(ValueError):
        model.response(0.0, 0.0, 0.5, 3.0)


def test_unsigned_square_retains_most_significant_bit():
    model = load("solutions", "prep_174_two_bit_unsigned_square")
    assert model.square(3) == 0b1001
    with pytest.raises(ValueError):
        model.square(-1)
