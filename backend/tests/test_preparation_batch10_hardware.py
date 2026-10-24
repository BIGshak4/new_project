"""Independent Boolean, state and complete small-network checks for 106/107/109."""
from __future__ import annotations

import ast
import importlib.util
import itertools
import json
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STORAGE = load("prep_106_sr_storage_gates")
LOWEST = load("prep_107_lowest_onehot_gates")
TRUTH = load("prep_109_truth_nand_nor")


def test_sr_latch_follows_history_and_rejects_forbidden_requests_instead_of_predicting_them():
    commands = ((0, 0), (1, 0), (0, 1))
    for initial in (0, 1):
        for length in range(8):
            for requests in itertools.product(commands, repeat=length):
                q = expected = initial
                for s, r in requests:
                    expected = 1 if s else 0 if r else expected
                    q = STORAGE.sr_latch(q, s, r)
                    assert q == expected
                    assert q == int(not (r or (1 - q)))
                    assert 1 - q == int(not (s or q))
        with pytest.raises(ValueError, match="outside"):
            STORAGE.sr_latch(initial, 1, 1)
        for s, r in itertools.product((0, 1), repeat=2):
            assert STORAGE.gated_sr_latch(initial, s, r, 0) == initial


def test_edge_extension_captures_at_rising_phase_without_assuming_matching_master_initial_state():
    legal = ((0, 0), (1, 0), (0, 1))
    for initial, master, request, later_request in itertools.product((0, 1), (0, 1), legal, legal):
        master, q = STORAGE.master_slave_phase(master, initial, *request, 0)
        assert q == initial
        master, q = STORAGE.master_slave_phase(master, q, *request, 1)
        expected = 1 if request[0] else 0 if request[1] else initial
        assert q == expected
        _, high_q = STORAGE.master_slave_phase(master, q, *later_request, 1)
        assert high_q == q


def test_lowest_onehot_matches_numerical_scan_and_parallel_prefix_from_prior_levels():
    for width in range(1, 13):
        for value in range(1 << width):
            expected = next((1 << index for index in range(width) if value // (2**index) % 2), 0)
            actual = LOWEST.lowest_onehot(value, width)
            assert actual == expected
            prefixes = [(value >> index) & 1 for index in range(width)]
            distance = 1
            while distance < width:
                previous = prefixes
                prefixes = [bit | (previous[index - distance] if index >= distance else 0)
                            for index, bit in enumerate(previous)]
                distance *= 2
            parallel = sum((((value >> index) & 1) and not (prefixes[index - 1] if index else 0)) << index
                           for index in range(width))
            assert parallel == actual
    assert f"{LOWEST.lowest_onehot(0b1110100, 7):07b}" == "0000100"
    for value, width in ((0, 0), (-1, 8), (256, 8), (True, 8)):
        with pytest.raises(ValueError):
            LOWEST.lowest_onehot(value, width)


def test_both_proposed_gate_libraries_match_every_given_row():
    expected = (0, 1, 0, 0, 1, 1, 0, 0)
    for index, (a, b, c) in enumerate(itertools.product((0, 1), repeat=3)):
        assert TRUTH.evaluate(a, b, c, TRUTH.NAND_NETLIST) == expected[index]
        assert TRUTH.evaluate(a, b, c, TRUTH.NOR_NETLIST) == expected[index]
    assert len(TRUTH.NAND_NETLIST) == 4 and len(TRUTH.NOR_NETLIST) == 2


def test_complete_up_to_three_nand_enumeration_excludes_target_and_one_nor_cannot_depend_on_three_inputs():
    # Represent functions by strings, independently of the check script's
    # integer truth words. Repeated wires and all older outputs remain available.
    inputs = [tuple((row >> bit) & 1 for row in range(8)) for bit in (2, 1, 0)]
    target = (0, 1, 0, 0, 1, 1, 0, 0)
    networks = [inputs]
    counts = []
    for _ in range(3):
        next_networks = []
        for wires in networks:
            for left, right in itertools.combinations_with_replacement(range(len(wires)), 2):
                result = tuple(int(not (a and b)) for a, b in zip(wires[left], wires[right], strict=True))
                assert result != target
                next_networks.append(wires + [result])
        counts.append(len(next_networks))
        networks = next_networks
    assert counts == [6, 60, 900]
    for left, right in itertools.combinations_with_replacement(range(3), 2):
        assert tuple(int(not (a or b)) for a, b in zip(inputs[left], inputs[right], strict=True)) != target
    for bit in range(3):
        assert any(target[row] != target[row ^ (1 << bit)] for row in range(8))


def test_evidence_scope_and_prompt_figure_do_not_claim_physical_simulation_or_reveal_circuit():
    for number in (106, 107, 109):
        evidence = json.loads((BANK / "checks" / f"prep-{number}-verification.json").read_text())
        assert evidence["status"] == "passed"
        assert "physical" in evidence["scope"] or "analog" in evidence["scope"]
    source = (BANK / "solutions/draw_prep_106_107_109.py").read_text(encoding="utf-8")
    prompt = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == "truth_prompt")
    prompt_source = ast.get_source_segment(source, prompt)
    assert "NOT B" not in prompt_source and "NAND: 4" not in prompt_source and "NOR: 2" not in prompt_source
    assert "0, 1, 0, 0, 1, 1, 0, 0" in prompt_source
