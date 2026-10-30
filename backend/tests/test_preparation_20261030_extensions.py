"""Executable checks for the two append-only October30 technical variants."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("stem", ["004_delayed_duty", "043_three_bit_symbols"])
def test_independent_extension_models(stem):
    path = ROOT / "interview_preparation/checks" / f"check_prep_{stem}.py"
    spec = importlib.util.spec_from_file_location("check_" + stem, path)
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    assert check.verify()["status"] == "passed"
