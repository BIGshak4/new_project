"""Numerical, interval and state contracts for PREP-115 and PREP-118."""
from __future__ import annotations

import importlib.util
import json
from math import isclose
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(folder, name):
    spec = importlib.util.spec_from_file_location(name, BANK / folder / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MOS = load("solutions", "prep_115_nmos_long_channel")
COMPARATOR = load("solutions", "prep_118_analog_threshold")


@pytest.mark.parametrize("number", (115, 118))
def test_independent_equation_or_history_checker_agrees_with_saved_evidence(number):
    result = load("checks", f"check_prep_{number}").run_checks()
    saved = json.loads((BANK / "checks" / f"prep-{number}-verification.json").read_text())
    assert result == saved
    assert result["status"] == "passed"
    assert "physical" in result["scope"] or "hardware" in result["scope"]


def test_long_channel_boundary_continuity_and_two_different_supply_bias_connections():
    beta, vt, gate = 0.001, 0.5, 1.5
    boundary = gate - vt
    left = MOS.nmos_current(gate, boundary - 1e-7, beta, vt)[1]
    right = MOS.nmos_current(gate, boundary + 1e-7, beta, vt)[1]
    assert isclose(left, right, rel_tol=1e-12)
    assert MOS.nmos_current(vt, 1, beta, vt) == ("cutoff", 0.0)
    assert MOS.nmos_current(gate, 0, beta, vt) == ("triode", 0.0)
    assert MOS.nmos_current(gate, 0.25, beta, vt)[1] == pytest.approx(0.00021875)
    assert MOS.nmos_current(gate, 2, beta, vt)[1] == pytest.approx(0.0005)
    assert MOS.nmos_current(gate, 3, beta, vt)[1] == MOS.nmos_current(gate, 2, beta, vt)[1]
    assert MOS.nmos_current(2, 2, beta, vt)[1] > MOS.nmos_current(gate, 2, beta, vt)[1]
    with pytest.raises(ValueError, match="saturation"):
        MOS.saturation_with_clm(gate, 0.25, beta, vt, 0.1)


def test_uncertainty_and_unknown_hysteresis_startup_do_not_invent_logic_values():
    assert COMPARATOR.compare_voltage(2, 2) is None
    assert COMPARATOR.compare_voltage(2.1, 2, 0.2) is None
    assert COMPARATOR.compare_voltage(2.3, 2, 0.2) == 1
    assert COMPARATOR.compare_voltage(1.7, 2, 0.2) == 0
    state = None
    observed = []
    for value in (0.5, 0.6, 1.1, 0.5, -0.1, 0.5):
        state = COMPARATOR.schmitt_step(value, 0, 1, state)
        observed.append(state)
    assert observed == [None, None, 1, 1, 0, 0]
