"""The ten-image intake adds nine review-pending questions and preserves its sources."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.engine.catalog import load_catalog
from app.engine.solution_review import solution_review
from app.services.question_resources import learner_media

ROOT = Path(__file__).resolve().parents[2]
SEEDS = ROOT / "backend/seeds"
NEW_IDS = {f"PREP-{number:03d}" for number in range(65, 74)}


def test_ten_sources_map_to_nine_new_questions_and_one_existing_identity():
    intake = json.loads((ROOT / "interview_preparation/intakes/2026-10-21-additional-sources.json").read_text("utf-8"))
    assert intake["source_count"] == len(intake["sources"]) == 10
    assert {item["preparation_id"] for item in intake["sources"]} == NEW_IDS | {"PREP-038"}
    for source in intake["sources"]:
        path = ROOT / "interview_preparation" / source["source_file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
    duplicate = next(item for item in intake["sources"] if item["preparation_id"] == "PREP-038")
    assert duplicate["decision"] == "additional_source_existing_question"


def test_new_questions_have_bilingual_study_material_without_inheriting_human_review():
    catalog = load_catalog(SEEDS)
    additions = [q for q in catalog.questions.values() if q.assets.get("preparation_id") in NEW_IDS]
    assert len(additions) == 9
    for question in additions:
        assert question.status == "trial" and question.reuse_status == "pending_review"
        assert not question.reviewed_by and not question.assets["assessment_ready"]
        assert solution_review(question).status == "pending_review"
        for language in ("he", "en"):
            text = question.text(language)
            assert text.prompt and text.reference_solution and len(text.hints) == 3
            assert len(set(text.hints)) == 3
            selected = learner_media(question.assets["bank_media"], language)
            assert selected and all(not item["source_path"].startswith("sources/") for item in selected)
            assert all(not item.get("language") or item["language"] == language for item in selected)


def test_fault_question_includes_authored_geometry_before_reveal_and_keeps_solution_separate():
    catalog = load_catalog(SEEDS)
    fault = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == "PREP-069")
    for language in ("he", "en"):
        media = learner_media(fault.assets["bank_media"], language)
        assert any(item["role"] == "prompt" and item["source_path"].startswith("diagrams/") for item in media)
        assert any(item["role"] == "solution" for item in media)
