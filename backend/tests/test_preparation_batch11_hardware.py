"""Complete small arithmetic/library checks for PREP-001/122 intake variants."""
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


@pytest.mark.parametrize("script,evidence", (("check_prep_001_five_input_fa", "prep-001-five-input-fa-verification.json"),
                                            ("check_prep_122", "prep-122-verification.json")))
def test_complete_arithmetic_and_component_library_checks_match_evidence(script, evidence):
    result = load("checks", script).run_checks()
    assert result == json.loads((BANK / "checks" / evidence).read_text())
    assert result["status"] == "passed"


def test_five_input_fa_outputs_are_count_bits_rather_than_parity_or_serial_state():
    model = load("solutions", "prep_001_five_input_fa")
    for value in range(32):
        signals = model.network(value)
        # Compare with all subsets of input positions; independent of FA logic.
        asserted_positions = [bit for bit in range(5) if value // (2**bit) % 2]
        assert model.popcount5(value) == len(asserted_positions)
        assert (signals["y2"], signals["y1"], signals["y0"]) == tuple(map(int, f"{len(asserted_positions):03b}"))
    assert model.popcount5(31) == 5


def test_ha_carry_combination_is_exclusive_and_preserves_full_fifth_output_bit():
    model = load("solutions", "prep_122_half_adder_only")
    for a in range(16):
        for b in range(16):
            rows = model.trace_add4(a, b)
            for row in rows[1:]:
                assert not (row["g"] and row["h"])
                assert row["discarded"] == 0
            assert model.add4(a, b) % 16 == (a + b) % 16
            assert rows[-1]["cout"] == int(a + b >= 16)
    assert model.add4(15, 15) == 0b11110
