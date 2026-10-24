"""Actual source-variant contracts and independent gate/timing checks."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"


def check_module(name):
    spec = importlib.util.spec_from_file_location(name, BANK / f"checks/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_xor_mux_timing_uses_full_path_and_independent_deadlines():
    result = check_module("check_prep_031_timing_variant").run_checks()
    assert result["xor_truth_rows"] == 4
    assert result["single_input_transition_cases"] == 8
    assert result["worst_transport_delay_ns"] == 4
    assert result["setup_arrival_deadline_cases"] == 48
    assert result["hold_arrival_deadline_cases"] == 36
    assert result["invalid_cases_rejected"] == 9


def test_single_enable_counter_exhaustive_oracles_and_original_specialization():
    result = check_module("check_prep_064_staged_enable").run_checks()
    assert result["state_enable_direction_cases"] == 40
    assert result["reset_priority_cases"] == 40
    assert result["eight_cycle_enable_streams"] == 5120
    assert result["original_control_specializations"] == 32
    assert result["invalid_cases_rejected"] == 8


@pytest.mark.parametrize("ident,source", [("PREP-031", 6), ("PREP-064", 10)])
def test_source_variants_have_bilingual_supplement_without_new_hint_queue(ident, source):
    archive = json.loads((BANK / "questions.json").read_text(encoding="utf-8"))
    record = next(q for q in archive["questions"] if q["id"] == ident)
    assert record["status"] == "in_review" and record["solution_status"] == "proposed"
    assert record["reviewed_by"] is None
    assert any(s.get("path") == f"sources/2026-10-24-batch30-{source:02}.png" for s in record["sources"])
    local = None
    for path in (ROOT / "backend/seeds/preparation_localization").glob("*.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        if ident in value:
            local = value[ident]
            break
    assert local is not None
    for language in ("he", "en"):
        variant = local["prompt_variants"][language]["batch30_variant"]
        assert len(variant["hints"]) == len(set(variant["hints"])) == 3
        assert variant["prompt"] in record["translations"][language]["prompt"]
        # Older PREP-031 stores only Hebrew prepared_hints; its English trio
        # already lives in translations/editorial. Preserve that arrangement.
        expected_prepared = 0 if ident == "PREP-031" and language == "en" else 3
        assert len([h for h in record["prepared_hints"] if h["language"] == language]) == expected_prepared
        assert len(record["translations"][language]["hints"]) == 3
        assert all(hint not in [h["content"] for h in record["prepared_hints"]] for hint in variant["hints"])
        assert "automatically" in local["prompt_variants"]["en"]["batch30_variant"]["integration_status"]
        assets = [a for a in record["media_assets"] if a.get("language") == language and "batch30" not in a["path"] and ("register-path-timing" in a["path"] or "staged-enable-counters" in a["path"])]
        assert len(assets) == 1
        assert assets[0]["type"] == "solution_diagram"
        assert (BANK / assets[0]["path"]).is_file()
