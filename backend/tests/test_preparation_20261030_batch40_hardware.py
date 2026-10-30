"""Independent model evidence for counter extension, NMOS load and hidden tree."""

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


@pytest.mark.parametrize("number", (152, 153, 154))
def test_checked_models_match_saved_independent_evidence(number):
    result = load("checks", f"check_prep_{number}").run_checks()
    assert result == json.loads((BANK / f"checks/prep-{number}-verification.json").read_bytes())
    assert result["status"] == "passed"


def test_counter_carry_uses_pre_edge_fifteen_and_wraps_high_bit():
    counter = load("solutions", "prep_152_extend_mod16_counter")
    assert counter.next_high(14, 0) == 0
    assert counter.next_high(15, 0) == 1
    assert counter.next_high(15, 1) == 0


def test_enhancement_load_high_is_degraded_and_single_pulldown_would_float():
    inverter = load("solutions", "prep_153_nmos_load_inverter")
    assert inverter.dc_output(0.0) == pytest.approx(4.0)
    assert 0 < inverter.dc_output(5.0) < 1.0
    assert inverter.dc_output(0.0, gamma=0.4) < 4.0
