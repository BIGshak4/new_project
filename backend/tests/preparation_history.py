"""Chained frozen projections preserve historical checks after append-only intake.

The fixture stores hashes and structure/length metadata, not replacement content.
Every original value remains checked. Each frozen intake separately names the
records allowed technical additions or provenance-only source additions.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

BASELINE = json.loads((Path(__file__).parent / "fixtures/preparation_before_batch90.json").read_bytes())
BATCH110_BASELINE = json.loads((Path(__file__).parent / "fixtures/preparation_before_batch110.json").read_bytes())
BATCH21_BASELINE = json.loads((Path(__file__).parent / "fixtures/preparation_before_20261031_batch21.json").read_bytes())
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


def _before_record(question, baseline):
    ident = question["id"]
    expected = baseline["records"][ident]
    if "projection" not in expected:
        assert digest(question) == expected["sha256"], ident
        return copy.deepcopy(question)
    projection = expected["projection"]
    assert set(projection["keys"]) <= question.keys(), ident
    restored = {key: copy.deepcopy(question[key]) for key in projection["keys"]}
    if ident in baseline["variant_ids"]:
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
        assert question.keys() - set(projection["keys"]) <= {
            "sources", "source_tags", "reported_companies", "source_topic_tags"
        }, ident
    transitions = projection.get("scalar_provenance_transitions", {}) | projection.get("scalar_revision_transitions", {})
    for key, transition in transitions.items():
        assert question[key] == transition["after"], (ident, key)
        restored[key] = transition["before"]
    for key, shape in projection["append_shapes"].items():
        restored[key] = _prefix(restored[key], shape, (ident, key))
    assert digest(restored) == expected["sha256"], ident
    return restored


def before_batch21_record(question):
    return _before_record(question, BATCH21_BASELINE)


def before_batch110_record(question):
    return _before_record(before_batch21_record(question), BATCH110_BASELINE)


def before_batch90_record(question):
    # First remove only the authorized later additions, then verify the older
    # snapshot. The old hash constants and both sets of prefix data stay intact.
    return _before_record(before_batch110_record(question), BASELINE)


def technical_before_batch110(question):
    question = before_batch110_record(question)
    return copy.deepcopy({key: question.get(key) for key in ("version", "translations", "prepared_hints")})


def technical_before_batch21(question):
    question = before_batch21_record(question)
    return copy.deepcopy({key: question.get(key) for key in ("version", "translations", "prepared_hints")})


def technical_before_batch90(question):
    question = before_batch90_record(question)
    return copy.deepcopy({key: question.get(key) for key in ("version", "translations", "prepared_hints")})


def _assert_archive(archive, baseline, restore):
    by_id = {question["id"]: question for question in archive["questions"]}
    assert set(baseline["record_order"]) <= by_id.keys()
    original = {key: archive[key] for key in baseline["top_level"]}
    assert archive["question_count"] == len(archive["questions"]) == 208
    original["question_count"] = baseline["top_level"]["question_count"]
    original["questions"] = [restore(by_id[ident]) for ident in baseline["record_order"]]
    assert digest(original) == baseline["canonical_sha256"]


def assert_pre_batch110_archive(archive):
    _assert_archive(archive, BATCH110_BASELINE, before_batch110_record)


def assert_pre_batch21_archive(archive):
    _assert_archive(archive, BATCH21_BASELINE, before_batch21_record)


def assert_pre_batch90_archive(archive):
    _assert_archive(archive, BASELINE, before_batch90_record)
    assert BASELINE["archive_byte_sha256"] == "5bae12aa23d16895bb038afbe068f2479c26dbf72048b937a5cb65119a520316"


def assert_pre_batch90_assets(uploads):
    """Every existing content-addressed asset and metadata entry must survive."""
    assert BASELINE["asset_sha256"].keys() <= uploads.keys()
    for path, previous_hash in BASELINE["asset_sha256"].items():
        assert digest(uploads[path]) == previous_hash, path


def assert_pre_batch110_assets(uploads):
    assert BATCH110_BASELINE["asset_sha256"].keys() <= uploads.keys()
    for path, previous_hash in BATCH110_BASELINE["asset_sha256"].items():
        assert digest(uploads[path]) == previous_hash, path


def assert_pre_batch21_assets(uploads):
    assert BATCH21_BASELINE["asset_sha256"].keys() <= uploads.keys()
    for path, previous_hash in BATCH21_BASELINE["asset_sha256"].items():
        assert digest(uploads[path]) == previous_hash, path


def assert_pre_batch21_localization(localization):
    """Localized material has its own frozen values and JSON types in both languages."""
    for ident, previous in BATCH21_BASELINE["localized_material"].items():
        current = localization[ident]
        restored = (_prefix(current, previous["append_shape"], ("localized_material", ident))
                    if "append_shape" in previous else current)
        assert digest(restored) == previous["sha256"], ("localized_material", ident)
