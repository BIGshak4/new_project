"""Frozen pre-batch90 projections, preserving historical checks after append-only intake.

The fixture stores hashes and structure/length metadata, not replacement content.
Every original value remains checked; only the seven authorized records may grow
technical material, and the two resubmissions may grow provenance alone.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

BASELINE = json.loads((Path(__file__).parent / "fixtures/preparation_before_batch90.json").read_bytes())
VARIANT_IDS = frozenset(BASELINE["variant_ids"])


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _prefix(value, shape, path):
    kind = shape["kind"]
    if kind == "str":
        assert isinstance(value, str) and len(value) >= shape["length"], path
        return value[:shape["length"]]
    if kind == "list":
        assert isinstance(value, list) and len(value) >= len(shape["items"]), path
        return [_prefix(value[i], item, (*path, i)) for i, item in enumerate(shape["items"])]
    if kind == "dict":
        assert isinstance(value, dict) and shape["items"].keys() <= value.keys(), path
        return {key: _prefix(value[key], item, (*path, key)) for key, item in shape["items"].items()}
    assert value == shape["value"] and type(value).__name__ == shape["type"], path
    return value


def before_batch90_record(question):
    ident = question["id"]
    expected = BASELINE["records"][ident]
    if "projection" not in expected:
        assert digest(question) == expected["sha256"], ident
        return copy.deepcopy(question)
    projection = expected["projection"]
    assert set(projection["keys"]) <= question.keys(), ident
    restored = {key: copy.deepcopy(question[key]) for key in projection["keys"]}
    if ident in VARIANT_IDS:
        assert question["version"] == projection["version"] + 1, ident
        restored["version"] = projection["version"]
        # These additions change the exercise, never its original hints or title.
        for language in ("he", "en"):
            original_fields = projection["append_shapes"]["translations"]["items"][language]["items"]
            assert question["translations"][language].keys() == original_fields.keys(), (ident, language)
            for field, previous_hash in projection["translation_immutable"][language].items():
                assert digest(question["translations"][language][field]) == previous_hash, (ident, language, field)
            for field in ("prompt", "reference_solution"):
                previous_length = projection["append_shapes"]["translations"]["items"][language]["items"][field]["length"]
                assert len(question["translations"][language][field]) > previous_length, (ident, language, field)
    else:
        assert question["version"] == projection["version"], ident
    for key, shape in projection["append_shapes"].items():
        restored[key] = _prefix(restored[key], shape, (ident, key))
    assert digest(restored) == expected["sha256"], ident
    return restored


def technical_before_batch90(question):
    if question["id"] in VARIANT_IDS:
        question = before_batch90_record(question)
    return copy.deepcopy({key: question.get(key) for key in ("version", "translations", "prepared_hints")})


def assert_pre_batch90_archive(archive):
    by_id = {question["id"]: question for question in archive["questions"]}
    assert set(BASELINE["record_order"]) <= by_id.keys()
    original = {key: archive[key] for key in BASELINE["top_level"]}
    assert archive["question_count"] == len(archive["questions"]) == 186
    original["question_count"] = BASELINE["top_level"]["question_count"]
    original["questions"] = [before_batch90_record(by_id[ident]) for ident in BASELINE["record_order"]]
    assert digest(original) == BASELINE["canonical_sha256"]
    assert BASELINE["archive_byte_sha256"] == "5bae12aa23d16895bb038afbe068f2479c26dbf72048b937a5cb65119a520316"


def assert_pre_batch90_assets(uploads):
    """Every existing content-addressed asset and metadata entry must survive."""
    assert BASELINE["asset_sha256"].keys() <= uploads.keys()
    for path, previous_hash in BASELINE["asset_sha256"].items():
        assert digest(uploads[path]) == previous_hash, path
