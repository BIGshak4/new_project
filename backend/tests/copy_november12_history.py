"""Reverse only hash-bound November 12 copy edits inside historical tests.

These projections never modify production objects, registries or approvals.
Explicit 700-expansion IDs are projected out before checking frozen 500-object
history. Both whole-object hashes and exact edited leaves remain checked before
returning the old copy to the pre-existing frozen-history layers.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"


def digest(value):
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


@cache
def fixture(kind):
    assert kind in {"example", "preparation", "fundamentals", "quiz"}, kind
    value = json.loads((FIXTURES / f"{kind}_copy_before_20261112.json").read_bytes())
    assert value["schema_version"] == 1
    return value


def is_700_addition(ident, *, variant=False):
    """Only the two explicitly allocated 251..350 ID ranges are additions.

    Unknown or malformed identities remain in the historical object so its
    recorded hash rejects them. New-content integrity is checked independently
    by the 700-expansion tests, rather than frozen pre-expansion snapshots.
    """
    pattern = r"quick-(?:hw|sw)-(\d+)-v[1-5]" if variant else r"quick-(?:hw|sw)-(\d+)"
    match = re.fullmatch(pattern, ident or "")
    return bool(match and 251 <= int(match[1]) <= 350)


def before_700_quiz_additions(key, actual):
    """Project only known 700 additions before strict November 12 copy hashes."""
    restored = copy.deepcopy(actual)
    if key == "duel_quiz.json":
        # Legacy standalone rows have no source_key and must remain untouched.
        restored["questions"] = [row for row in restored["questions"]
                                 if not is_700_addition(row.get("source_key"))]
        current = "Quiz-duel content: 700 short-question sources with five authored bilingual variants each (3500), "
        previous = "Quiz-duel content: 500 short-question sources with five authored bilingual variants each (2500), "
        if restored.get("_about", "").startswith(current):
            restored["_about"] = previous + restored["_about"][len(current):]
    elif key == "release-manifest.json":
        restored["questions"] = [row for row in restored["questions"]
                                 if not is_700_addition(row.get("key"), variant=True)]
    return restored


def before_current_copy(kind, key, actual):
    """Restore recorded text; every unrelated value remains hash-checked."""
    catalog = fixture(kind)
    records = catalog["files"] if kind == "fundamentals" else catalog["entries"]
    record = records.get(key)
    restored = before_700_quiz_additions(key, actual) if kind == "quiz" else copy.deepcopy(actual)
    if record is None:
        return restored  # The caller's unchanged historical hash still applies.
    assert digest(restored) == record["after_sha256"], ("nov12_current", kind, key)
    if kind == "fundamentals":
        by_id = {card["id"]: card for card in restored}
        assert len(by_id) == len(restored)
        for change in record["changes"]:
            field, language = change["field"], change["language"]
            assert field in {"title", "prompt", "answer", "takeaway"}
            assert language in {"he", "en"}
            text = by_id[change["id"]][field][language]
            for start, end, previous in reversed(change["splices"]):
                assert 0 <= start <= end <= len(text)
                assert isinstance(previous, str)
                text = text[:start] + previous + text[end:]
            by_id[change["id"]][field][language] = text
    else:
        for change in record["changes"]:
            path = change["path"]
            assert path and all(isinstance(part, (str, int)) for part in path)
            assert "solution_review" not in path
            node = restored
            for part in path[:-1]:
                node = node[part]
            editorial_flag = ["assets", "preparation_resource", "website_editorial", "learner_text_edited"]
            if "splices" in change:
                assert path != editorial_flag
                assert "before" not in change and "after" not in change
                text = node[path[-1]]
                assert isinstance(text, str)
                assert digest(text) == change["after_sha256"], ("nov12_leaf_current", kind, key, path)
                previous_end = 0
                for start, end, previous in change["splices"]:
                    assert isinstance(start, int) and isinstance(end, int)
                    assert previous_end <= start <= end <= len(text)
                    assert isinstance(previous, str)
                    previous_end = end
                for start, end, previous in reversed(change["splices"]):
                    text = text[:start] + previous + text[end:]
                assert digest(text) == change["before_sha256"], ("nov12_leaf_history", kind, key, path)
                node[path[-1]] = text
                continue
            elif path == editorial_flag:
                assert change["before"] is False and change["after"] is True
            else:
                assert isinstance(change["before"], str) and isinstance(change["after"], str)
            assert node[path[-1]] == change["after"], (kind, key, path)
            node[path[-1]] = change["before"]
        for addition in record.get("added_copy_dates", []):
            # The quiz release manifest records which hashes were renewed by
            # this wording-only pass. No approval/status field is removable.
            assert kind == "quiz" and key == "release-manifest.json"
            path = addition["path"]
            assert len(path) == 3 and path[0] == "questions" and isinstance(path[1], int)
            assert path[2] == "wording_updated_on" and addition["after"] == "2026-11-12"
            node = restored["questions"][path[1]]
            assert node[path[2]] == addition["after"]
            del node[path[2]]
        removed = record.get("removed_review_metadata", {})
        assert set(removed) <= {"solution_review"}
        if removed:
            # Historical approval restoration is test-only and must match the
            # unchanged actual registry and the restored old solution content.
            from app.engine.solution_review import solution_content_hash

            assert "solution_review" not in restored["assets"]
            registry = json.loads((ROOT / "backend/seeds/solution_review_attestations.json").read_bytes())
            registered = registry["questions"][restored["key"]]
            assert removed["solution_review"] == registered
            assert solution_content_hash(restored) == registered["content_sha256"]
            restored["assets"]["solution_review"] = copy.deepcopy(registered)
    assert digest(restored) == record["before_sha256"], ("nov12_history", kind, key)
    return restored


def before_current_fundamentals_bytes(name, actual):
    """Preserve pre-copy byte checks, including JSON formatting and ordering."""
    record = fixture("fundamentals")["files"][name]
    text = actual.replace(b"\r\n", b"\n").decode("utf-8")
    assert hashlib.sha256(text.encode()).hexdigest() == record["after_byte_sha256"]
    previous = before_current_copy("fundamentals", name, json.loads(text))
    previous_end = 0
    for start, end, old_text in record["text_splices"]:
        assert previous_end <= start <= end <= len(text) and isinstance(old_text, str)
        previous_end = end
    for start, end, old_text in reversed(record["text_splices"]):
        text = text[:start] + old_text + text[end:]
    assert json.loads(text) == previous
    result = text.encode()
    assert hashlib.sha256(result).hexdigest() == record["before_byte_sha256"]
    return result


def before_current_fundamentals_manifest(actual):
    """Check every old card hash, restore copy, then omit only 700 additions."""
    restored = copy.deepcopy(actual)
    for name in fixture("fundamentals")["files"]:
        cards = json.loads((ROOT / "apps/web/src/content" / name).read_bytes())
        previous = before_current_copy("fundamentals", name, cards)
        for current, old in zip(cards, previous, strict=True):
            ident = current["id"]
            assert actual["questions"][ident] == digest(current), ("nov12_revision", ident)
            restored["questions"][ident] = digest(old)
    restored["questions"] = {ident: value for ident, value in restored["questions"].items()
                             if not is_700_addition(ident)}
    return restored
