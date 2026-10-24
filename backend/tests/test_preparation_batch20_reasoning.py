"""Contracts and independent RC/rendezvous checks for the batch20 intake."""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import itertools
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def record(ident):
    questions = json.loads((BANK / "questions.json").read_text(encoding="utf-8"))["questions"]
    return next(question for question in questions if question["id"] == ident)


def material(ident):
    for path in (ROOT / "backend/seeds/preparation_localization").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if ident in data:
            return data[ident]
    pytest.fail(f"Missing paired material for {ident}")


def text_leaves(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from text_leaves(child)
    elif isinstance(value, list):
        for child in value:
            yield from text_leaves(child)


def test_099_paired_content_source_and_proposed_status():
    question = record("PREP-099")
    assert question["key"] == "measure-capacitance-rc-step-response"
    assert question["solution_status"] == "proposed"
    assert question["status"] == "in_review"
    assert question["reviewed_by"] is None
    assert question["reported_companies"] == ["NVIDIA"]
    assert question["difficulty"] is None
    assert any(source["path"] == "sources/2026-10-24-batch20-07.png"
               for source in question["sources"])
    assert "ערך כלשהוא" in question["original_prompt"]
    for language in ("he", "en"):
        translation = question["translations"][language]
        hints = [hint["content"] for hint in question["prepared_hints"]
                 if hint["language"] == language]
        assert len(hints) == len(set(hints)) == 3
        assert hints == translation["hints"]
        assert "100 nF" in translation["reference_solution"]
        assert "Cx = tau / Rth - Cp" in translation["reference_solution"]
        assert "https://www.picotech.com/" in translation["reference_solution"]
        assert "Rth = Rseries || Rp" in translation["reference_solution"]
    localized = material("PREP-099")
    assert set(localized) == {
        "assumptions", "optimality", "verification", "edge_cases", "common_mistakes",
        "interview_answer", "source_ambiguities", "solution_extensions", "technical_references",
        "relationship_note",
    }
    for field, pair in localized.items():
        assert set(pair) == {"he", "en"}
        assert pair["en"] == question[field]
        assert all(not any("\u0590" <= char <= "\u05ff" for char in leaf)
                   for leaf in text_leaves(pair["en"]))
        assert any(any("\u0590" <= char <= "\u05ff" for char in leaf)
                   for leaf in text_leaves(pair["he"]))
    assert all(media["type"] == "solution_diagram"
               for media in question["media_assets"] if media["path"].startswith("diagrams/"))
    assert len([media for media in question["media_assets"]
                if media["type"] == "solution_diagram"]) == 4


def test_099_network_inference_against_decimal_and_independent_kcl():
    check = load_module("batch20_rc_check", BANK / "checks/check_prep_099.py")
    result = check.run_checks()
    assert result["status"] == "passed"
    assert result["network_inference_cases"] == 192
    assert result["decimal_transition_checks"] == 960
    assert result["independent_kcl_rk4_cases"] == 48
    assert result["invalid_cases_rejected"] == 12
    assert result["example_capacitance_farad"] == 1e-7


def test_099_a_single_unloaded_curve_cannot_separate_unknown_r_and_c():
    model = load_module("batch20_rc_scale", BANK / "solutions/prep_099_rc_capacitance.py")
    r, c = 1000, 1e-6
    tau = r * c
    curves = []
    for scale in (0.01, 0.5, 1, 2, 100):
        new_r, new_c = r * scale, c / scale
        assert new_r * new_c == pytest.approx(tau)
        curves.append([model.transition_voltage(time, new_r * new_c)
                       for time in (0, tau, 2 * tau, 5 * tau)])
    for curve in curves:
        assert curve == pytest.approx(curves[0])


def test_062_d_is_append_only_and_preserves_old_prepared_hints():
    question = record("PREP-062")
    old_prefixes = {
        ("he", "prompt"): (2456, "fc383f573e5e0850461cd12819a7769c019eb2688c2774a743918a286aa0c972"),
        ("he", "reference_solution"): (5888, "a6602860ba89cc59096cb1d0165754ed85f100a895497fd84605fbd1b6c29bb9"),
        ("en", "prompt"): (3071, "ebe610d60fc99fa1cd0ce0dbf8f6bd1f9e51df995d2ff065d177d032b217ae95"),
        ("en", "reference_solution"): (7239, "6fbb8897fc57a9f3f4c51bbf2611410fd007af2316e1607bd65c3860abdd5c03"),
    }
    for (language, field), (length, digest) in old_prefixes.items():
        value = question["translations"][language][field]
        assert len(value) > length
        assert hashlib.sha256(value[:length].encode()).hexdigest() == digest
    digest = hashlib.sha256(json.dumps(
        question["prepared_hints"], ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()
    assert digest == "d310da1b089dfb40cbb540997226fd0ab069c6e9d65eddb7b1705f9419c25a4a"
    localized = material("PREP-062")
    for language in ("he", "en"):
        assert len(localized["prompt_variants"][language]["D"]["hints"]) == 3
        assert localized["optimality"][language]["variant_d"]
        assert localized["source_ambiguities"][language]["variant_d"]
    assert "solutions/prep_062_d_flags_no_meeting_sensor.py" in question["solution_code_paths"]
    assert any(source["path"] == "sources/2026-10-24-batch20-06.png"
               for source in question["sources"])


def test_062_d_trajectory_formula_and_out_of_contract_counterexamples():
    check = load_module("batch20_d_check", BANK / "checks/check_prep_062_d.py")
    result = check.run_checks()
    assert result["status"] == "passed"
    assert result["integer_distance_cases"] == 772
    assert result["trajectory_points_vs_independent_formula"] == 201984
    assert result["half_integer_counterexamples"] == 3


def test_062_d_local_controller_uses_marker_only_and_always_executes_timed_action():
    model = load_module("batch20_d_controller", BANK / "solutions/prep_062_d_flags_no_meeting_sensor.py")
    assert list(inspect.signature(model.FlagProgram.command).parameters) == ["self", "flag_here"]
    for flags in itertools.product((False, True), repeat=8):
        controller = model.FlagProgram()
        actions = [controller.command(flag) for flag in flags]
        assert all(action in {"right", "wait"} for action in actions)
        assert actions[0] == "right"
    result = model.simulate(3)
    assert result["first_meeting"] == 10
    assert len(result["actions"]) > result["first_meeting"]
    assert result["trajectory"][-1][0] != result["trajectory"][-1][1]
