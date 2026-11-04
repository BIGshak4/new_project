"""Copy deployment planning is offline, field-scoped, and refuses live drift."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/prepare_question_copy_sync.py"
SPEC = importlib.util.spec_from_file_location("prepare_question_copy_sync", PATH)
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


def fixture():
    text = {"title": "Old title", "prompt": "Old prompt", "requirements": "Old requirements",
            "reference_solution": "Old solution", "hints": ["one", "two", "three"],
            "common_errors": {"mistake": "Old explanation"}, "accepted_approaches": ["Old approach"], "choices": None}
    question = {"key": "test-copy", "status": "trial", "skills": [{"skill": "logic", "weight": 1}],
                "deterministic_check": {"args": [""]}, "translations": {"en": deepcopy(text), "he": deepcopy(text)},
                "assets": {"titles": {"he": "Old title", "en": "Old title"}, "assessment_ready": False,
                           "solution_review": {"content_sha256": "old-approved", "status": "human_reviewed"},
                           "preparation_resource": {"learner_material": {"assumptions": {"he": ["Old assumption"], "en": ["Existing"]}},
                                                    "original_prompt": "Preserve archive", "verification_script_path": "scripts/check.py"},
                           "bank_media": [{"source_path": "diagrams/one.png", "path": "seed/path.png", "caption": "Old caption", "role": "solution", "language": "he"}]}}
    row = {"id": "id-one", "key": "test-copy", "status": "trial", "reviewed_by": None, "times_served": 40,
           "review_notes": "Live review note", "assets": deepcopy(question["assets"]),
           "requirements": text["requirements"], "reference_solution": text["reference_solution"],
           "hints": deepcopy(text["hints"]), "accepted_approaches": deepcopy(text["accepted_approaches"]),
           "common_errors": [{"key": "mistake", "core": True, "skill": "logic", "tip_id": "live-tip", "explanation": "Old explanation"}],
           "choices": None}
    row["assets"].update({"assessment_ready": True, "content_hash": "old-hash", "live_only": {"untouched": True}})
    row["assets"]["bank_media"][0]["path"] = "uploaded/immutable.png"
    translations = [{"question_id": "id-one", "language": language,
                     **{field: deepcopy(value) for field, value in text.items() if field not in {"title", "accepted_approaches"}},
                     "parity_checked": True, "parity_checked_by": "reviewer", "updated_at": "timestamp"}
                    for language in ("he", "en")]
    live = {"test-copy": {"question": row, "translations": translations,
                          "skills": [{"question_id": "id-one", "skill_id": "skill-one", "weight": 1, "is_primary": True}]}}
    return {"test-copy": question}, live


def plan(old, new, live):
    return sync.build_plan(old, new, live, hash_function=lambda _: "new-hash", solution_hash_function=lambda _: "new-approved")


def test_copy_patches_preserve_live_identity_media_review_parity_and_skills():
    old, live = fixture()
    new = deepcopy(old)
    q = new["test-copy"]
    q["translations"]["he"]["prompt"] = "New prompt"
    q["translations"]["en"]["hints"][1] = "New hint"
    q["translations"]["en"]["common_errors"]["mistake"] = "New explanation"
    q["assets"]["bank_media"][0]["caption"] = "New caption"
    q["assets"]["preparation_resource"]["learner_material"]["assumptions"]["he"][0] = "New assumption"
    q["assets"].pop("solution_review")
    snapshot = deepcopy(live)
    result = plan(old, new, live)
    assert not result["conflicts"] and not result["rejected_seed_changes"]
    assert live == snapshot  # no in-place edits to backups
    item = result["items"][0]
    after = item["after"]
    assert after["hints"] == ["one", "New hint", "three"]
    assert after["common_errors"] == [{"key": "mistake", "core": True, "skill": "logic", "tip_id": "live-tip", "explanation": "New explanation"}]
    assert after["assets"]["bank_media"][0]["path"] == "uploaded/immutable.png"
    assert after["assets"]["bank_media"][0]["caption"] == "New caption"
    assert after["assets"]["live_only"] == {"untouched": True}
    assert after["assets"]["assessment_ready"] is True
    assert "solution_review" not in after["assets"]
    assert after["assets"]["content_hash"] == "new-hash"
    assert after["review_notes"] == "Live review note"
    assert after["status"] == "trial" and after["id"] == "id-one"
    assert item["skills"] == live["test-copy"]["skills"]
    assert all(x["after"]["parity_checked"] is True and x["after"]["parity_checked_by"] == "reviewer" for x in item["translations"])


def test_changed_leaf_conflicts_with_live_edit_but_untouched_sibling_survives():
    old, live = fixture()
    new = deepcopy(old)
    new["test-copy"]["translations"]["en"]["hints"][0] = "New first hint"
    live["test-copy"]["question"]["hints"][2] = "Live third hint"
    result = plan(old, new, live)
    assert not result["conflicts"]
    assert result["items"][0]["after"]["hints"] == ["New first hint", "two", "Live third hint"]
    live["test-copy"]["question"]["hints"][0] = "Someone edited first hint"
    result = plan(old, new, live)
    assert not result["items"]
    assert result["conflicts"][0]["path"] == ["hints", 0]
    assert result["conflicts"][0]["live"] == {"value": "Someone edited first hint"}


def test_matching_live_attestation_survives_even_if_absent_from_local_registry():
    old, live = fixture()
    new = deepcopy(old)
    new["test-copy"]["translations"]["he"]["hints"][0] = "New hint outside solution fingerprint"
    new["test-copy"]["assets"].pop("solution_review")
    live["test-copy"]["question"]["assets"]["solution_review"]["content_sha256"] = "new-approved"
    result = plan(old, new, live)
    after = result["items"][0]["after"]["assets"]
    assert after["solution_review"] == live["test-copy"]["question"]["assets"]["solution_review"]
    assert after["assessment_ready"] is True


@pytest.mark.parametrize("path,value", [
    (("status",), "published"),
    (("skills", 0, "weight"), .5),
    (("skills", 0, "weight"), True),
    (("deterministic_check", "args"), []),
    (("assets", "bank_media", 0, "path"), "replacement.png"),
    (("assets", "preparation_resource", "verification_script_path"), "other.py"),
    (("assets", "preparation_resource", "original_prompt"), "New raw archive"),
    (("translations", "he", "parity_checked"), True),
])
def test_noncopy_seed_changes_are_rejected(path, value):
    old, live = fixture()
    new = deepcopy(old)
    sync.set_path(new["test-copy"], path, value)
    result = plan(old, new, live)
    assert not result["items"]
    assert result["rejected_seed_changes"]


def test_missing_backups_and_changed_translation_inventory_are_conflicts():
    old, live = fixture()
    new = deepcopy(old)
    new["test-copy"]["translations"]["he"]["prompt"] = "Changed"
    assert plan(old, new, {})["conflicts"]
    live["test-copy"]["translations"].pop()
    assert plan(old, new, live)["conflicts"][0]["reason"] == "translation languages differ from baseline"


@pytest.mark.parametrize("before,after", [
    (0, 1), (False, True), ("0", 0),
    ({"state": 0, "next": 1}, {"state": 1, "next": 0}),
    ([{"bits": 2}], ["two bits"]),
    ("Before\n```c\nreturn 0;\n```", "After\n```c\nreturn 1;\n```"),
    ("Formula \\(A+B\\)", "Formula \\(A-B\\)"),
])
def test_material_edits_cannot_mutate_timing_table_values_booleans_code_or_math(before, after):
    assert not sync.allowed(("assets", "preparation_resource", "transition_tables", "he"), before, after)
    assert not sync.allowed(("assets", "preparation_resource", "learner_material", "truth_table", "he"), before, after)


def test_copy_lists_and_wording_around_unchanged_code_remain_allowed():
    path = ("assets", "preparation_resource", "learner_material", "editorial_notes", "he")
    assert sync.allowed(path, ["Useful note", "Retired note"], ["Useful note"])
    assert sync.allowed(path, "Old wording\n```c\nreturn 0;\n```", "New wording\n```c\nreturn 0;\n```")


def test_bilingual_wrappers_preserve_technical_paths_values_and_language_agreement():
    original = {"count": 8, "rows": [[0, 1], [1, 0]], "enabled": False, "text": "Old prose"}
    localized = {"he": deepcopy(original), "en": deepcopy(original)}
    localized["he"]["text"] = "Updated prose"
    assert sync.localized_material_preserves_data(original, localized)
    swapped = deepcopy(localized)
    swapped["he"]["rows"] = [[1, 0], [0, 1]]
    assert not sync.localized_material_preserves_data(original, swapped)
    disagree = deepcopy(localized)
    disagree["en"]["count"] = 7
    assert not sync.localized_material_preserves_data(original, disagree)
    incomplete = deepcopy(localized)
    incomplete["en"].pop("count")
    assert not sync.localized_material_preserves_data(original, incomplete)
    moved = deepcopy(localized)
    for language in ("he", "en"):
        moved[language]["other_count"] = moved[language].pop("count")
    assert not sync.localized_material_preserves_data(original, moved)
    removed = deepcopy(localized)
    for language in ("he", "en"):
        removed[language].pop("enabled")
    assert not sync.localized_material_preserves_data(original, removed)


def test_material_wrapper_does_not_bypass_protected_code_guard():
    original = {"count": 8, "text": "```c\nreturn 0;\n```"}
    localized = {"he": deepcopy(original), "en": deepcopy(original)}
    localized["en"]["text"] = "```c\nreturn 1;\n```"
    assert not sync.localized_material_preserves_data(original, localized)


def test_generated_sql_locks_checks_full_preimages_and_defaults_to_rollback():
    text = sync.sql([])
    assert text.endswith("ROLLBACK;\n")
    assert sync.sql([], commit=True).endswith("COMMIT;\n")
    assert "FOR UPDATE" in text and "FOR SHARE" in text
    assert "ARRAY['updated_at','times_served']" in text
    assert "Concurrent translation change" in text and "Concurrent skill links change" in text
    assert "Unexpected question postimage" in text
    assert "DELETE " not in text and "INSERT " not in text
    update = text[text.index("UPDATE public.question SET"):text.index("GET DIAGNOSTICS affected = ROW_COUNT;", text.index("UPDATE public.question SET"))]
    for forbidden in ("status =", "reviewed_by =", "review_notes =", "subject_id =", "rubric =", "times_served ="):
        assert forbidden not in update
