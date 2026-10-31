"""Attested solution correctness never grants broader publication/assessment approval."""
from __future__ import annotations

import copy
import importlib.util
import json
import uuid
from pathlib import Path

import pytest
from app.engine.catalog import load_catalog
from app.engine.solution_review import attach_registered_reviews, solution_content_hash, solution_review
from app.repo.questions import LoadedQuestion, detail, summary

BACKEND = Path(__file__).resolve().parents[1]
REVISED_SOLUTION_KEY = "prep-seventeen-prisoners-two-mandatory-switches"
REVISED_ROBOT_KEY = "prep-identical-robots-trains-static-marker-rendezvous"
REVISED_SOLUTION_KEYS = {
    REVISED_SOLUTION_KEY, REVISED_ROBOT_KEY,
    "prep-xor-mux-zero-only", "prep-one-two-missing-values", "prep-three-bit-up-down-counter-gates",
    "prep-eight-bit-popcount-adders", "prep-three-color-in-place-partition",
    "prep-twenty-one-prisoners-one-light",
    "prep-circuit-from-clock-input-output-waveforms", "prep-serial-safe-abcd-sequence-detector",
    "prep-twenty-five-horses", "prep-dark-room-ten-tails-equal-groups",
    "prep-balanced-brackets-mixed-text", "prep-doorway-occupancy-two-sensors",
    "prep-sixteen-input-interrupt-controller",
    "prep-random-permutation-fisher-yates",
    "prep-bridge-torch-twelve-hours",
    "prep-boolean-function-two-muxes",
    "prep-serial-binary-divisibility-by-three-fsm",
}


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(BACKEND / "seeds")


def test_frozen_attestation_covers_only_existing_snapshot(catalog):
    registry = json.loads((BACKEND / "seeds/solution_review_attestations.json").read_text(encoding="utf-8"))
    assert len(registry["questions"]) == 93
    for question in catalog.questions.values():
        if question.key not in registry["questions"] or question.key in REVISED_SOLUTION_KEYS:
            assert solution_review(question).status == "pending_review"
            assert solution_review(question).reviewed_on is None
            continue
        assert solution_review(question).model_dump() == {
            "status": "human_reviewed", "reviewed_on": "2026-10-21"}
        assert not question.reviewed_by and question.reuse_status == "pending_review"
        assert not question.languages_ready(), "Solution correctness does not grant translation parity"
        row = LoadedQuestion(uuid.uuid4(), question, question.version)
        safe = summary(row, "he")
        assert safe.solution_review.status == "human_reviewed"
        assert detail(row, "en").solution_review.status == "human_reviewed"
        assert "content_sha256" not in safe.model_dump()["solution_review"]
        if question.assets.get("preparation_id"):
            assert not safe.assessment_ready and not safe.reviewed


def test_prisoner_explanation_revision_preserves_but_does_not_inherit_old_attestation(catalog):
    registry = json.loads((BACKEND / "seeds/solution_review_attestations.json").read_text(encoding="utf-8"))
    old_record = registry["questions"][REVISED_SOLUTION_KEY]
    assert old_record["content_sha256"] == "dc0d3fb8884814753227eafc4ab665268015b129f4f1958ea291fb2b127477f6"
    assert old_record["status"] == "human_reviewed" and old_record["reviewed_on"] == "2026-10-21"
    question = catalog.questions[REVISED_SOLUTION_KEY]
    assert solution_content_hash(question) != old_record["content_sha256"]
    assert "solution_review" not in question.assets
    assert solution_review(question).model_dump() == {"status": "pending_review", "reviewed_on": None}
    row = LoadedQuestion(uuid.uuid4(), question, question.version)
    for language in ("he", "en"):
        assert summary(row, language).solution_review.status == "pending_review"
        assert detail(row, language).solution_review.status == "pending_review"
    reviewed = {q.key for q in catalog.questions.values() if solution_review(q).status == "human_reviewed"}
    assert len(reviewed) == 74
    assert reviewed == set(registry["questions"]) - REVISED_SOLUTION_KEYS


def test_robot_rewrite_keeps_frozen_attestation_without_approving_new_sensing_contract(catalog):
    registry = json.loads((BACKEND / "seeds/solution_review_attestations.json").read_text(encoding="utf-8"))
    old_record = registry["questions"][REVISED_ROBOT_KEY]
    assert old_record["content_sha256"] == "9838d558893d4a2faeb5480b3a09885a2df4951ddc97c2f73ad2a871823571a2"
    assert old_record["status"] == "human_reviewed" and old_record["reviewed_on"] == "2026-10-21"
    question = catalog.questions[REVISED_ROBOT_KEY]
    assert solution_content_hash(question) != old_record["content_sha256"]
    assert "solution_review" not in question.assets
    assert solution_review(question).model_dump() == {"status": "pending_review", "reviewed_on": None}
    row = LoadedQuestion(uuid.uuid4(), question, question.version)
    for language in ("he", "en"):
        assert summary(row, language).solution_review.status == "pending_review"
        assert detail(row, language).solution_review.status == "pending_review"


@pytest.mark.parametrize("change", ["reference", "prompt", "technical_material", "media", "code", "correct_choice"])
def test_changed_content_loses_attestation(catalog, change):
    question = next(q.model_copy(deep=True) for q in catalog.questions.values()
                    if q.assets.get("preparation_id") == "PREP-060")
    if change in {"reference", "prompt"}:
        field = "reference_solution" if change == "reference" else "prompt"
        setattr(question.translations["he"], field, getattr(question.translations["he"], field) + " changed")
    elif change == "technical_material":
        question.assets["preparation_resource"]["learner_material"]["new_explanation"] = "changed"
    elif change == "media":
        question.assets["bank_media"].append({"path": "diagrams/new.png", "sha256": "new", "role": "solution"})
    elif change == "code":
        question.assets["shared_code"] = "changed()"
    else:
        question.correct_choice = 1
    assert solution_review(question).status == "pending_review"
    assert solution_review(question).reviewed_on is None


def test_operational_metadata_and_private_sources_do_not_change_scope(catalog):
    question = next(q.model_copy(deep=True) for q in catalog.questions.values()
                    if q.assets.get("preparation_id") == "PREP-002")
    baseline = solution_content_hash(question)
    question.times_served += 7
    question.assets["content_hash"] = "operational"
    question.assets["assessment_ready"] = True
    question.assets["bank_media"].append({"source_path": "sources/internal.png", "path": "private", "sha256": "other"})
    assert solution_content_hash(question) == baseline
    assert solution_review(question).status == "human_reviewed"


def test_new_questions_do_not_inherit_a_global_review(catalog):
    question = next(iter(catalog.questions.values())).model_dump(mode="json")
    question["key"] = "new-unreviewed-question"
    registry = json.loads((BACKEND / "seeds/solution_review_attestations.json").read_text(encoding="utf-8"))
    attach_registered_reviews([question], registry)
    assert "solution_review" not in question["assets"]
    assert solution_review(question).status == "pending_review"


def test_registry_cannot_reapprove_an_edited_revision(catalog):
    question = next(iter(catalog.questions.values())).model_dump(mode="json")
    question["translations"]["en"]["reference_solution"] += " changed"
    registry = json.loads((BACKEND / "seeds/solution_review_attestations.json").read_text(encoding="utf-8"))
    attach_registered_reviews([question], registry)
    assert "solution_review" not in question["assets"]


def test_assets_only_update_requires_matching_snapshot(catalog):
    spec = importlib.util.spec_from_file_location("review_update", BACKEND / "scripts/prepare_solution_review_update.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    registry = json.loads((BACKEND / "seeds/solution_review_attestations.json").read_text(encoding="utf-8"))
    question = next(iter(catalog.questions.values())).model_dump(mode="json")
    sql = module.prepare([question], registry)
    assert "for update" in sql and "current_content is distinct" in sql
    assert "perform t.question_id from public.question_translation t" in sql
    assert "where t.question_id = locked_id order by t.language for update" in sql
    assert "update public.question set assets =" in sql
    assert "reviewed_by =" not in sql and "assessment_ready =" not in sql
    changed = copy.deepcopy(question)
    changed["translations"]["he"]["reference_solution"] += " changed"
    with pytest.raises(ValueError, match="No matching existing attestation"):
        module.prepare([changed], registry)


def test_solution_review_metadata_does_not_reset_general_seed_approval(catalog):
    spec = importlib.util.spec_from_file_location("review_seed_db", BACKEND / "scripts/seed_db.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    question = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == "PREP-002")
    before = question.model_copy(deep=True)
    before.assets.pop("solution_review")
    assert module.content_hash(before) == module.content_hash(question)
