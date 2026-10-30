"""Independent bounded logical checks for new 30-October hardware records."""

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


@pytest.mark.parametrize("number", (139, 140, 145, 147))
def test_independent_model_results_match_recorded_coverage(number):
    actual = load("checks", f"check_prep_{number}").run_checks()
    saved = json.loads((BANK / "checks" / f"prep-{number}-verification.json").read_bytes())
    assert actual == saved and actual["status"] == "passed"


def test_ninth_bit_and_terminal_square_edges():
    address = load("solutions", "prep_145_address_size_single_incrementer")
    assert address.address_plus_size(255, 1) == (True, 256)
    assert address.address_plus_size(255, 2) == (True, 257)
    assert address.address_plus_size(255, 4) == (True, 259)
    assert address.address_plus_size(0, 3) == (False, 0)
    square = load("solutions", "prep_140_cycle_and_square")
    assert square.trace(2, 4) == [(0, 0), (1, 1), (2, 4), (2, 4), (2, 4)]
    assert square.widths(0) == (1, 1)


def test_xor_swap_equal_values_and_all_zero_are_not_lost():
    swap = load("solutions", "prep_147_complementary_load_alu_swap")
    assert swap.swap_trace(7, 7, 3) == [(7, 7), (0, 7), (0, 7), (7, 7)]
    assert swap.swap_trace(0, 0, 1)[-1] == (0, 0)
