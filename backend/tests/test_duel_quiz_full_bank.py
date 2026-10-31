"""Full-bank coverage, editorial hygiene, and reproducible computed case checks.

These tests intentionally do not confer human approval or claim perfect spelling.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.duels import DuelService, load_quiz

ROOT = Path(__file__).resolve().parents[2]
AUTHORING = ROOT / "backend/scripts/quiz_authoring"
SHARDS = ROOT / "backend/seeds/duel_quiz_batches"


def module(name):
    spec = importlib.util.spec_from_file_location(f"quiz_author_{name}", AUTHORING / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_complete_bank_has_valid_bilingual_text_and_source_ids():
    assembler = module("assemble")
    data, checks, errors, numbers = assembler.collect()
    assert not errors
    assert len(assembler.reviewed_number_flags(data["questions"], numbers)) == len(numbers)
    assert len(checks) == 2450
    assert read(ROOT / "backend/seeds/duel_quiz.json") == data
    assert len(load_quiz(ROOT / "backend/seeds/duel_quiz.json")) == 2540


@pytest.mark.parametrize("name", ["hardware_basic", "hardware_advanced", "reasoning", "code", "hardware_400", "reasoning_400", "code_400",
                                  "hardware_500", "reasoning_500", "code_500"])
def test_authored_cases_recompute_and_match_saved_output(name):
    author = module(name)
    # Each author exposes verification in build(). A generated JSON edit cannot
    # silently diverge from the executable case inventory.
    result = author.build()
    questions = result[0] if isinstance(result, tuple) else result
    assert questions == read(SHARDS / f"{name}.json")


def test_new_variants_have_content_bound_pilot_authorization():
    assembler = module("assemble")
    data = read(ROOT / "backend/seeds/duel_quiz.json")
    new = [
        q for q in data["questions"] if q.get("source_key") and q["source_key"] not in assembler.PILOT_SOURCES
    ]
    assert len(new) == 2450
    assert all(q["status"] == "approved" for q in new)
    for q in new:
        approval = q["release_approval"]
        assert approval["basis"] == "user_authorized_pilot_release"
        assert approval["professional_review"] == "pending"
        assert approval["content_sha256"] == assembler.content_digest(q)
        assert not any(
            "`" in text
            for values in [q["prompt"], q["explanation"], *q["choices"]]
            for text in values.values()
        )
    pilot = [q for q in data["questions"] if q.get("source_key") in assembler.PILOT_SOURCES]
    assert len(pilot) == 50
    assert all(
        q["status"] == "approved" and q["release_approval"]["professional_review"] == "pending" for q in pilot
    )


def test_production_pool_contains_all_linked_sources_and_excludes_legacy_drafts():
    quiz = load_quiz(ROOT / "backend/seeds/duel_quiz.json")
    service = DuelService(None, None, None, SimpleNamespace(rules=None), quiz=quiz)
    assert len(service.quiz_pool()) == 2500
    assert set(service.quiz_groups()) == set(module("assemble").source_cards())
    assert all(len(items) == 5 for items in service.quiz_groups().values())


def test_release_rejects_content_changed_after_authorization():
    assembler = module("assemble")
    questions = read(SHARDS / "code.json")
    manifest = read(SHARDS / "release-manifest.json")
    subset = {
        **manifest,
        "questions": [
            entry for entry in manifest["questions"] if entry["key"] in {q["key"] for q in questions}
        ],
    }
    changed = copy.deepcopy(questions)
    changed[0]["choices"][0]["en"] += " changed"
    with pytest.raises(AssertionError, match="Release content changed"):
        assembler.apply_release(changed, subset)


@pytest.mark.asyncio
async def test_operational_summary_reports_pool_counts_without_answers(monkeypatch):
    from app.engine.catalog import load_catalog
    from app.main import app, catalog_summary

    quiz = load_quiz(ROOT / "backend/seeds/duel_quiz.json")
    duels = DuelService(None, None, None, SimpleNamespace(rules=None), quiz=quiz)
    runtime = SimpleNamespace(catalog=load_catalog(ROOT / "backend/seeds"), duels=duels)
    monkeypatch.setattr(app.state, "runtime", runtime, raising=False)
    summary = await catalog_summary()
    assert summary["quiz_source_count"] == 500
    assert summary["quiz_variant_count"] == 2500
    assert not ({"choices", "correct", "explanation", "prompt"} & summary.keys())
