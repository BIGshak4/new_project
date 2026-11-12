"""The test-only copy projection must not forgive unrelated mutations."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from tests import copy_november12_history as history


@pytest.mark.parametrize("name", sorted(history.fixture("fundamentals")["files"]))
def test_fundamentals_restore_exact_prior_hash_without_mutating_current(name):
    cards = json.loads((history.ROOT / "apps/web/src/content" / name).read_bytes())
    unchanged = copy.deepcopy(cards)
    result = history.before_current_copy("fundamentals", name, cards)
    assert history.digest(result) == history.fixture("fundamentals")["files"][name]["before_sha256"]
    assert cards == unchanged


@pytest.mark.parametrize("name", sorted(history.fixture("fundamentals")["files"]))
def test_fundamentals_restore_prior_bytes_and_reject_reformatting(name):
    raw = (history.ROOT / "apps/web/src/content" / name).read_bytes()
    result = history.before_current_fundamentals_bytes(name, raw)
    assert hashlib.sha256(result).hexdigest() == history.fixture("fundamentals")["files"][name]["before_byte_sha256"]
    with pytest.raises(AssertionError):
        history.before_current_fundamentals_bytes(name, raw + b" ")


@pytest.mark.parametrize("change", ["unrecorded_text", "identity", "metadata"])
def test_fundamentals_reject_unrecorded_mutations(change):
    name = "fundamentals-code-250.json"
    cards = json.loads((history.ROOT / "apps/web/src/content" / name).read_bytes())
    if change == "unrecorded_text":
        cards[0]["prompt"]["en"] += " Extra requirement."
    elif change == "identity":
        cards[0]["id"] += "-different"
    else:
        cards[0]["difficulty"] = 10
    with pytest.raises(AssertionError, match="nov12_current"):
        history.before_current_copy("fundamentals", name, cards)


def test_generic_projection_checks_whole_objects_and_exact_text_leaves(monkeypatch):
    before = {"text": {"en": "Old wording."}, "score": 4}
    after = {"text": {"en": "Revised wording."}, "score": 4}
    record = {"before_sha256": history.digest(before), "after_sha256": history.digest(after),
              "changes": [{"path": ["text", "en"], "before": "Old wording.", "after": "Revised wording."}]}
    monkeypatch.setattr(history, "fixture", lambda _: {"entries": {"item": record}})
    assert history.before_current_copy("example", "item", after) == before
    assert after["text"]["en"] == "Revised wording."
    with pytest.raises(AssertionError, match="nov12_current"):
        history.before_current_copy("example", "item", {**after, "score": 5})
    record["changes"][0]["before"] = "An unrecorded old wording."
    with pytest.raises(AssertionError, match="nov12_history"):
        history.before_current_copy("example", "item", after)


def test_compact_projection_checks_leaf_hashes_and_splice_bounds(monkeypatch):
    before = {"text": "A prior word and another word.", "score": 4}
    after = {"text": "A newer word and another word.", "score": 4}
    change = {"path": ["text"], "before_sha256": history.digest(before["text"]),
              "after_sha256": history.digest(after["text"]), "splices": [[2, 7, "prior"]]}
    record = {"before_sha256": history.digest(before), "after_sha256": history.digest(after),
              "changes": [change]}
    monkeypatch.setattr(history, "fixture", lambda _: {"entries": {"item": record}})
    assert history.before_current_copy("example", "item", after) == before
    assert after["text"] == "A newer word and another word."
    change["splices"][0][2] = "wrong"
    with pytest.raises(AssertionError, match="nov12_leaf_history"):
        history.before_current_copy("example", "item", after)
    change["splices"] = [[2, 7, "prior"], [3, 8, "overlap"]]
    with pytest.raises(AssertionError):
        history.before_current_copy("example", "item", after)
    change["splices"] = [[2, 999, "out of range"]]
    with pytest.raises(AssertionError):
        history.before_current_copy("example", "item", after)


def test_only_recorded_quiz_wording_dates_can_be_removed(monkeypatch):
    before = {"questions": [{"key": "item", "authored_sha256": "unchanged"}]}
    after = copy.deepcopy(before)
    after["questions"][0]["wording_updated_on"] = "2026-11-12"
    addition = {"path": ["questions", 0, "wording_updated_on"], "after": "2026-11-12"}
    record = {"before_sha256": history.digest(before), "after_sha256": history.digest(after),
              "changes": [], "added_copy_dates": [addition]}
    monkeypatch.setattr(history, "fixture", lambda _: {"entries": {"release-manifest.json": record}})
    assert history.before_current_copy("quiz", "release-manifest.json", after) == before
    assert after["questions"][0]["wording_updated_on"] == "2026-11-12"
    addition["path"][-1] = "authored_sha256"
    with pytest.raises(AssertionError):
        history.before_current_copy("quiz", "release-manifest.json", after)


def quiz_path(name):
    base = history.ROOT / "backend/seeds"
    return base / name if name == "duel_quiz.json" else base / "duel_quiz_batches" / name


@pytest.mark.parametrize("name,count", [("duel_quiz.json", 2540), ("release-manifest.json", 2450)])
def test_700_additions_project_to_exact_recorded_quiz_history_without_mutation(name, count):
    actual = json.loads(quiz_path(name).read_bytes())
    unchanged = copy.deepcopy(actual)
    current_old = history.before_700_quiz_additions(name, actual)
    record = history.fixture("quiz")["entries"][name]
    assert history.digest(current_old) == record["after_sha256"]
    previous = history.before_current_copy("quiz", name, actual)
    assert len(previous["questions"]) == count
    assert history.digest(previous) == record["before_sha256"]
    assert actual == unchanged
    if name == "duel_quiz.json":
        assert sum(not row.get("source_key") for row in previous["questions"]) == 40


@pytest.mark.parametrize("name", ["duel_quiz.json", "release-manifest.json"])
@pytest.mark.parametrize("mutation", ["content", "identity", "old_disguised_as_new", "remove", "order", "metadata"])
def test_700_projection_still_rejects_every_unrecorded_old_quiz_mutation(name, mutation):
    actual = json.loads(quiz_path(name).read_bytes())
    # The first two records belong to the protected history, including legacy
    # standalone rows in the bank and old approved entries in its manifest.
    first = actual["questions"][0]
    if mutation == "content":
        if name == "duel_quiz.json":
            first["prompt"]["en"] += " Unrecorded change."
        else:
            first["authored_sha256"] = "0"*64
    elif mutation == "identity":
        first["key"] = "quick-sw-999-v1"
    elif mutation == "old_disguised_as_new":
        if name == "duel_quiz.json":
            first["source_key"] = "quick-sw-251"
        else:
            first["key"] = "quick-sw-251-v1"
    elif mutation == "remove":
        del actual["questions"][0]
    elif mutation == "order":
        actual["questions"][0], actual["questions"][1] = actual["questions"][1], actual["questions"][0]
    else:
        actual["unexpected_metadata"] = True
    with pytest.raises(AssertionError, match="nov12_current"):
        history.before_current_copy("quiz", name, actual)


def test_700_projection_rejects_unrecorded_about_changes():
    actual = json.loads(quiz_path("duel_quiz.json").read_bytes())
    actual["_about"] += " An unrelated metadata change."
    with pytest.raises(AssertionError, match="nov12_current"):
        history.before_current_copy("quiz", "duel_quiz.json", actual)


def test_700_projection_identifies_only_allocated_new_ranges():
    for ident in ("quick-hw-251", "quick-sw-320", "quick-sw-350"):
        assert history.is_700_addition(ident)
        assert history.is_700_addition(ident+"-v5", variant=True)
    for ident in (None, "quiz-legacy", "quick-sw-250", "quick-hw-999", "quick-sw-251-altered"):
        assert not history.is_700_addition(ident)
    assert not history.is_700_addition("quick-sw-251-v6", variant=True)


def test_pre700_revision_projection_matches_frozen_history_and_rejects_old_hash_edit():
    actual = json.loads((history.ROOT / "backend/seeds/fundamentals_catalog.json").read_bytes())
    unchanged = copy.deepcopy(actual)
    previous = history.before_current_fundamentals_manifest(actual)
    baseline = json.loads((history.FIXTURES / "preparation_before_20261108_batch20.json").read_bytes())
    assert len(previous["questions"]) == 500
    assert history.digest(previous) == baseline["fundamentals_catalog_sha256"]
    assert actual == unchanged
    actual["questions"]["quick-sw-01"] = "0"*64
    with pytest.raises(AssertionError, match="nov12_revision"):
        history.before_current_fundamentals_manifest(actual)
