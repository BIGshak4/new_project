"""Bilingual learner explanations are complete, while source records stay intact."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "backend/scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_bilingual_material_covers_every_visible_nonempty_field_and_keeps_author_data():
    builder = module("build_preparation_bank")
    original = json.loads((ROOT / "interview_preparation/questions.json").read_text(encoding="utf-8-sig"))
    built, _ = builder.load()
    resources = {q["assets"]["preparation_id"]: q["assets"]["preparation_resource"] for q in built}
    for source in original["questions"]:
        resource = resources[source["id"]]
        paired = resource["learner_material"]
        required = {key for key in builder.MATERIAL_FIELDS if resource.get(key) not in (None, "", [], {})}
        assert set(paired) == required, source["id"]
        for key in required:
            assert set(paired[key]) == {"he", "en"}
            assert resource[key] == builder.strip_personal(source[key]), (source["id"], key)


def test_missing_or_one_sided_technical_translations_cannot_be_compiled():
    builder = module("build_preparation_bank")
    question = {"id": "PREP-TEST", "assumptions": ["An explicit assumption"]}
    for edits in ({}, {"PREP-TEST": {}}, {"PREP-TEST": {"assumptions": {"he": ["הנחה"]}}},
                  {"PREP-TEST": {"assumptions": {"he": [], "en": ["An assumption"]}}}):
        with pytest.raises(ValueError):
            builder.learner_material(question, edits)


def test_content_sync_requires_the_same_archive_and_does_not_mutate_inputs():
    sync = module("sync_material_localization")
    compiled = {"assets": {"preparation_id": "PREP-001", "source_sha256": "source",
                           "preparation_resource": {"learner_material": {"assumptions": {"he": ["הנחה"], "en": ["Assumption"]}}}}}
    live = {"preparation_id": "PREP-001", "source_sha256": "source",
            "preparation_resource": {"id": "PREP-001", "assumptions": ["Source wording"]},
            "assessment_ready": False, "content_hash": "existing-review-revision"}
    before = copy.deepcopy(live)
    patch = sync.patch_for(live, compiled)
    assert patch == compiled["assets"]["preparation_resource"]["learner_material"]
    assert live == before
    for key, value in (("source_sha256", "other"), ("preparation_id", "PREP-002"),
                       ("preparation_resource", {"id": "PREP-002"})):
        changed = {**live, key: value}
        with pytest.raises(ValueError):
            sync.patch_for(changed, compiled)


def test_sync_checks_database_identity_independently_of_the_api_url():
    sync = module("sync_material_localization")
    assert sync.database_belongs_to_project("postgresql+asyncpg://postgres:p@db.expected.supabase.co/postgres", "expected")
    assert sync.database_belongs_to_project("postgresql://postgres.expected:p@aws-0-eu.pooler.supabase.com/postgres", "expected")
    for url in ("postgresql://postgres.other:p@aws-0-eu.pooler.supabase.com/postgres",
                "postgresql://postgres:p@db.other.supabase.co/postgres",
                "postgresql://postgres.expected:p@unrelated.example/postgres",
                "postgresql://postgres:p@localhost/postgres", ""):
        assert not sync.database_belongs_to_project(url, "expected")
