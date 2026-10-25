"""Numeric source specialization remains in-place, linear and honest about swaps."""
import importlib.util
from pathlib import Path


def test_numeric_partition_actual_code_and_access_bounds():
    path = Path(__file__).resolve().parents[2] / "interview_preparation/checks/check_prep_019_numeric_variant.py"
    spec = importlib.util.spec_from_file_location("numeric_partition_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.verify()
    assert result["exhaustive_ternary_words"] == 9841
    assert result["random_arrays"] == 300
