"""Source contracts plus independent epistemic/graph checks for PREP-113/114."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"


def load_check(number):
    name = f"batch10_reasoning_check_{number}"
    spec = importlib.util.spec_from_file_location(name, BANK / f"checks/check_prep_{number}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def question(ident):
    archive = json.loads((BANK / "questions.json").read_text(encoding="utf-8"))
    return next(item for item in archive["questions"] if item["id"] == ident)


def localized_material(ident):
    for path in (ROOT / "backend/seeds/preparation_localization").glob("*.json"):
        chunk = json.loads(path.read_text(encoding="utf-8"))
        if ident in chunk:
            return chunk[ident]
    pytest.fail(f"Missing localized material {ident}")


def leaves(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from leaves(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from leaves(item)


@pytest.mark.parametrize("ident", ("PREP-113", "PREP-114"))
def test_full_bilingual_reasoning_content_remains_proposed_and_diagrams_are_gated(ident):
    record = question(ident)
    assert record["solution_status"] == "proposed" and record["status"] == "in_review"
    assert record["reviewed_by"] is None and record["difficulty"] is None
    # Preserve this intake's attribution while later supplied sources may add companies.
    assert {"NVIDIA"} <= set(record["reported_companies"])
    for lang in ("he", "en"):
        hints = [hint["content"] for hint in record["prepared_hints"] if hint["language"] == lang]
        assert len(hints) == len(set(hints)) == 3
        assert record["translations"][lang]["hints"] == hints
        assert record["translations"][lang]["reference_solution"].strip()
    material = localized_material(ident)
    assert set(material) == {
        "assumptions", "optimality", "edge_cases", "common_mistakes", "interview_answer",
        "source_ambiguities", "verification", "relationship_note", "solution_extensions",
    }
    for field, pair in material.items():
        assert set(pair) == {"he", "en"}
        assert pair["en"] == record[field]
        assert all(not any("\u0590" <= char <= "\u05ff" for char in text)
                   for text in leaves(pair["en"]))
        assert any(any("\u0590" <= char <= "\u05ff" for char in text)
                   for text in leaves(pair["he"]))
    diagrams = [asset for asset in record["media_assets"] if asset["path"].startswith("diagrams/")]
    assert len(diagrams) == 2
    assert all(asset["type"] == "solution_diagram" for asset in diagrams)
    assert {asset["language"] for asset in diagrams} == {"he", "en"}


def test_113_source_underdetermination_is_not_hidden_by_the_edited_answer():
    record = question("PREP-113")
    assert "באוויר" in record["original_prompt"]
    assert "200" in record["original_prompt"] and "4:00" in record["original_prompt"]
    assert "פעם אחת" not in record["original_prompt"]
    for lang, required in (
        ("he", ("חייבת", "פעם אחת", "00:00", "03:00", "ראשונים", "חסרות")),
        ("en", ("must signal exactly once", "first signals", "00:00", "03:00", "simultaneous", "common knowledge")),
    ):
        prompt = record["translations"][lang]["prompt"]
        assert all(token in prompt for token in required)
    assert "source alone has no unique answer" in record["translations"]["en"]["reference_solution"]
    assert "five liars" in record["translations"]["en"]["reference_solution"]
    result = load_check(113).run_checks()
    assert result["explicit_nonempty_worlds"] == 1013
    assert result["first_signal_actor_checks"] == 4097
    assert result["without_common_fact_worlds_unresolved"] == 1022
    assert result["source_only_counterexamples"] == 2
    assert result["next_morning_elapsed_rounds"] == 5


def test_114_exact_four_guest_couples_and_simple_graph_contract():
    record = question("PREP-114")
    assert "עוד 4 זוגות" in record["original_prompt"]
    prompt = record["translations"]["en"]["prompt"]
    assert "exactly four" in prompt and "ten people" in prompt
    assert "at most once" in prompt and "only the prince" in prompt
    assert "also shook four" in record["translations"]["en"]["reference_solution"]
    result = load_check(114).run_checks()
    assert result["all_small_graphs"] == 4113
    assert result["valid_small_graphs"] == 11
    assert result["valid_by_guest_couples"] == {0: 1, 1: 2, 2: 8}
    assert result["constructed_larger_graphs"] == 21
    assert result["four_guest_example_degrees"] == [4, 4, 0, 8, 1, 7, 2, 6, 3, 5]
