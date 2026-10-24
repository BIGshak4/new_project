"""Actual comparator and inverted-input gate models, no live database."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "interview_preparation"


def model(name, folder="solutions"):
    spec = importlib.util.spec_from_file_location(name, ROOT / folder / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_comparator_and_gate_models_against_independent_oracles():
    result = model("check_prep_110_112", "checks").verify()
    assert result["four_bit_pairs"] == 256
    assert result["two_gate_mixed_no_constant_networks"] == 72


@pytest.mark.parametrize("a,b,width", [(-1, 0, 4), (0, 16, 4), (1, 0, 0), (True, 0, 4)])
def test_comparator_rejects_invalid_words(a, b, width):
    with pytest.raises(ValueError):
        model("prep_110_unsigned_comparator").compare_words(a, b, width)


def test_gate_models_reject_nonbinary_input():
    with pytest.raises(ValueError):
        model("prep_112_and_from_inverted_input_gates").both_with_zero(2, 0)
