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
