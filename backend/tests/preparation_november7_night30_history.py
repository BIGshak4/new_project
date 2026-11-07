"""Hash-bound reverse projection for the authorized November 7 fourth intake only.

This test-only layer precedes the existing learner-copy and older intake layers.
It cannot forgive a changed old prefix, title, hint, asset or unrelated value.
"""
from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def prefix(value, shape, path=()):
    kind = shape["kind"]
    if kind == "str":
        assert isinstance(value, str) and len(value) >= shape["length"], path
        return value[:shape["length"]]
    if kind == "list":
        assert isinstance(value, list) and len(value) >= len(shape["items"]), path
        return [prefix(value[i], item, (*path, i)) for i, item in enumerate(shape["items"])]
    if kind == "dict":
        assert isinstance(value, dict) and shape["items"].keys() <= value.keys(), path
        return {key: prefix(value[key], item, (*path, key)) for key, item in shape["items"].items()}
    assert value == shape["value"] and type(value).__name__ == shape["type"], path
    return value


@lru_cache(maxsize=1)
def baseline():
    return json.loads((Path(__file__).parent / "fixtures/preparation_before_20261107_night30.json").read_bytes())


@lru_cache(maxsize=1)
def compiled_projections():
    return json.loads((Path(__file__).parent / "fixtures/preparation_compiled_before_20261107_night30.json").read_bytes())["records"]


def before_batch1107n30_compiled(question):
    ident = question["assets"]["preparation_id"]
    if ident not in baseline()["records"]:
        return copy.deepcopy(question)
    frozen = compiled_projections().get(ident)
    if frozen is None:
        assert digest(question) == baseline()["compiled_sha256"][question["key"]], ident
        return copy.deepcopy(question)
    current = copy.deepcopy(question)
    raw_path = Path(__file__).resolve().parents[2] / "interview_preparation/questions.json"
    raw = next(q for q in json.loads(raw_path.read_bytes())["questions"] if q["id"] == ident)
    assert current["assets"]["source_sha256"] == hashlib.sha256(json.dumps(raw, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    current["assets"]["source_sha256"] = frozen["source_sha256_before"]
    for transition in frozen["transitions"]:
        node = current
        for key in transition["path"][:-1]:
            node = node[key]
        key = transition["path"][-1]
        assert node[key] == transition["after"], (ident, transition["path"])
        node[key] = copy.deepcopy(transition["before"])
    for field, metadata in frozen["removed_review_metadata"].items():
        assert field not in current["assets"], (ident, field)
        current["assets"][field] = copy.deepcopy(metadata)
    for index, item in enumerate(current["assets"]["bank_media"], 1):
        assert item["id"] == f"asset-{index}", (ident, index)
    media = {item["path"]: item for item in current["assets"]["bank_media"]}
    assert len(media) == len(current["assets"]["bank_media"])
    for path, previous in frozen["media_sha256"].items():
        media[path]["id"] = frozen["media_ids"][path]
        assert digest(media[path]) == previous, (ident, path)
    current["assets"]["bank_media"] = [media[path] for path in frozen["media_order"]]
    restored = prefix(current, frozen["shape"], ("compiled", ident))
    assert digest(restored) == frozen["sha256"] == baseline()["compiled_sha256"][question["key"]]
    return restored


def before_batch1107n30_localized(ident, value):
    if ident not in baseline()["localized_material"]:
        return copy.deepcopy(value)
    frozen = baseline()["localized_material"][ident]
    restored = prefix(value, frozen["append_shape"], ("localized", ident)) if "append_shape" in frozen else copy.deepcopy(value)
    assert digest(restored) == frozen["sha256"], ("localized", ident)
    return restored
