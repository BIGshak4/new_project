"""Reverse only the recorded November 4 short-card wording edit for old hashes.

Every current file and restored file is bound to its complete object hash. The
fixture was captured from immutable commit 08ea983, before the authorized copy
edit; it contains only learner-text splices, never identity or grading edits.
"""
from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from tests.copy_november12_history import before_current_copy, before_current_fundamentals_manifest

ROOT = Path(__file__).resolve().parents[2]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@lru_cache(maxsize=1)
def fixture():
    return json.loads((Path(__file__).parent / "fixtures/fundamentals_copy_before_20261104.json").read_bytes())


def before_learner_copy_short_file(name, cards):
    cards = before_current_copy("fundamentals", name, cards)
    frozen = fixture()["files"][name]
    assert digest(cards) == frozen["after_sha256"], ("short_copy_current", name)
    result = copy.deepcopy(cards)
    by_id = {card["id"]: card for card in result}
    assert len(by_id) == len(result)
    for change in frozen["changes"]:
        field, language = change["field"], change["language"]
        assert field in {"title", "prompt", "answer", "takeaway"}
        text = by_id[change["id"]][field][language]
        for start, end, previous in reversed(change["splices"]):
            text = text[:start] + previous + text[end:]
        by_id[change["id"]][field][language] = text
    assert digest(result) == frozen["before_sha256"], ("short_copy_history", name)
    return result


def before_learner_copy_short_manifest(manifest):
    """Preserve the old 250-card manifest hash without replacing live revisions."""
    manifest = before_current_fundamentals_manifest(manifest)
    baseline = json.loads((Path(__file__).parent / "fixtures/preparation_before_20261107_batch30.json").read_bytes())
    assert digest(manifest) == baseline["fundamentals_catalog_sha256"]
    result = copy.deepcopy(manifest)
    for name in fixture()["files"]:
        cards = json.loads((ROOT / "apps/web/src/content" / name).read_bytes())
        original = {card["id"]: card for card in before_current_copy("fundamentals", name, cards)}
        for current, previous in zip(cards, before_learner_copy_short_file(name, cards), strict=True):
            ident = current["id"]
            assert manifest["questions"][ident] == digest(original[ident])
            if int(ident.rsplit("-", 1)[1]) <= 125:
                result["questions"][ident] = digest(previous)
    return result
