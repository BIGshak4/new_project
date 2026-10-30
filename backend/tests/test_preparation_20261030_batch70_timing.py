"""Independent load, timing-window and capacitive-charge model evidence."""

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


def test_independent_evidence_and_saved_case_counts():
    result = load("checks", "check_prep_175_177").run_checks()
    assert result == {"case_counts": {175: 29, 176: 54, 177: 33}, "rejected_invalid_parameters": 5}
    for number, count in result["case_counts"].items():
        saved = json.loads((BANK / f"checks/prep-{number}-verification.json").read_bytes())
        assert saved["status"] == "passed"
        assert saved["independent_cases"] == count


def test_buffer_is_not_a_free_delay_improvement():
    model = load("solutions", "prep_175_buffer_load_model")
    direct, buffered = model.compare_paths(1000, 100e-12, 2e-12, 50, 1e-9)
    assert direct == pytest.approx(69.314718e-9)
    assert buffered == pytest.approx(5.852030e-9)
    direct, buffered = model.compare_paths(1000, 0.1e-12, 2e-12, 50, 1e-9)
    assert direct < buffered


def test_positive_capture_skew_helps_setup_and_hurts_hold():
    model = load("solutions", "prep_176_setup_hold_budgets")
    base = model.timing_slacks(2, 0.08, 0.2, 0.05, 1.7, 0.15, 0.1, 0, 0.03, 0.02)
    later = model.timing_slacks(2, 0.08, 0.2, 0.05, 1.7, 0.15, 0.1, 0.2, 0.03, 0.02)
    assert base == pytest.approx((-0.08, 0.01))
    assert later[0] - base[0] == pytest.approx(0.2)
    assert later[1] - base[1] == pytest.approx(-0.2)


def test_no_coupling_removes_neighbor_dependence():
    model = load("solutions", "prep_177_capacitive_crosstalk")
    assert [model.effective_capacitance(3, 0, ratio) for ratio in (-1, 0, 1)] == [3, 3, 3]
    assert model.effective_capacitance(3, 2, -1) == 7
    assert model.effective_capacitance(3, 2, 1) == 3
