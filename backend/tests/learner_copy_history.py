"""Exact reverse projection for the user-authorized 2026-11-04 learner-copy edit.

This is test-only: verify the whole current object before reversing the recorded
wording delta, then run the existing historical hashes and append-only checks.
Nothing is read from production history or regenerated during a test run.
"""
from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from tests.preparation_november7_history import before_batch1107_compiled, before_batch1107_localized


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@lru_cache(maxsize=1)
def _fixtures():
    return json.loads((Path(__file__).parent / "fixtures/learner_copy_before_20261104.json").read_bytes())


def _before_copy(kind, key, value):
    frozen = _fixtures()[kind].get(key)
    if frozen is None:
        return copy.deepcopy(value)
    assert _digest(value) == frozen["after_sha256"], ("learner_copy_current", kind, key)
    result = copy.deepcopy(value)
    for change in frozen["changes"]:
        node = result
        for field in change["path"][:-1]:
            node = node[field]
        field = change["path"][-1]
        if change.get("remove"):
            del node[field]
        elif "splices" in change:
            text = node[field]
            for start, end, replacement in reversed(change["splices"]):
                text = text[:start] + replacement + text[end:]
            node[field] = text
        else:
            node[field] = copy.deepcopy(change["before"])
    assert _digest(result) == frozen["before_sha256"], ("learner_copy_history", kind, key)
    return result


def before_learner_copy_compiled(question):
    question = before_batch1107_compiled(question)
    return _before_copy("compiled", question["key"], question)


def before_learner_copy_localized(ident, value):
    value = before_batch1107_localized(ident, value)
    return _before_copy("localized", ident, value)


@lru_cache(maxsize=1)
def _compiled_sources():
    path = Path(__file__).resolve().parents[1] / "seeds/questions/preparation_bank.json"
    return {question["key"]: question for question in json.loads(path.read_bytes())}


def before_learner_copy_text(key, language, field, actual):
    """Bind a catalog text value to its source before verifying an older prefix."""
    source = _compiled_sources()[key]
    assert actual == source["translations"][language][field], (key, language, field)
    return before_learner_copy_compiled(source)["translations"][language][field]
