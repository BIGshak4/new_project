"""The November wording edit must preserve exercises and executable examples.

Expected invariants were captured from the pre-edit 08ea983 catalog, independently
of the text replacement code. They deliberately retain empty grading inputs.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from tests.preparation_november7_history import baseline, before_batch1107_compiled

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/learner_copy_invariants_20261104.json"


def read(path):
    return json.loads(path.read_bytes())


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def long_questions():
    return [q for name in ("example", "preparation")
            for q in read(ROOT / f"backend/seeds/questions/{name}_bank.json")]


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def controls(question):
    fields = ("key", "version", "status", "origin", "format", "practice_modes", "subject",
              "difficulty", "estimated_minutes", "archetype", "skills", "rubric", "common_errors",
              "deterministic_check", "check_self_test", "correct_choice", "reuse_status", "reviewed_by")
    assets = question.get("assets", {})
    return {**{key: question.get(key) for key in fields}, "asset_controls": {
        key: assets.get(key) for key in ("collection", "preparation_id", "assessment_ready",
            "difficulty_status", "source_difficulty", "category", "topics", "reported_companies",
            "company_attribution_status", "related_question_ids", "source_sha256", "shared_code", "code_language")}}


def code_blocks(question):
    return {lang: {field: re.findall(r"```[\s\S]*?```", question["translations"][lang][field])
                   for field in ("prompt", "requirements", "reference_solution")}
            for lang in ("he", "en")}


def test_all_long_question_identities_grading_and_code_are_unchanged():
    expected = read(FIXTURE)
    questions = sorted(long_questions(), key=lambda q: q["key"])
    assert len(questions) == 331
    previous = [before_batch1107_compiled(q) if q.get("assets", {}).get("preparation_id") else q
                for q in questions if not q.get("assets", {}).get("preparation_id")
                or q["assets"]["preparation_id"] in baseline()["records"]]
    assert len(previous) == 285
    assert digest([controls(q) for q in previous]) == expected["long_controls_sha256"]
    assert digest({q["key"]: code_blocks(q) for q in previous}) == expected["long_code_blocks_sha256"]
    balanced = next(q for q in questions if q["key"] == "example-balanced-brackets")
    assert balanced["deterministic_check"]["spec"]["cases"][3]["args"] == [""]
    missing = next(q for q in questions if q["key"] == "prep-one-two-missing-values")
    assert "שני החסרים בסעיף ב דורשים N−2 ערכים שונים." in missing["translations"]["he"]["prompt"]


def test_short_identity_code_and_quiz_correct_choices_survive_copy_changes():
    expected = read(FIXTURE)
    cards = [q for path in (ROOT / "apps/web/src/content").glob("fundamentals-*.json")
             if path.name != "fundamentals-revisions.json" for q in read(path)]
    assert len(cards) == 500
    controls_only = [{k: v for k, v in q.items() if k not in ("title", "prompt", "answer", "takeaway")}
                     for q in sorted(cards, key=lambda q: q["id"])]
    assert digest(controls_only) == expected["short_controls_sha256"]
    quiz = read(ROOT / "backend/seeds/duel_quiz.json")["questions"]
    quiz_controls = [{k: q.get(k) for k in ("key", "source_key", "variant", "topic", "correct", "status")}
                     for q in sorted(quiz, key=lambda q: q["key"])]
    assert len(quiz) == 2540
    assert digest(quiz_controls) == expected["quiz_controls_sha256"]


def test_visible_copy_has_familiar_terms_and_no_retired_release_notes():
    material = []
    for q in long_questions():
        material.extend(strings(q["translations"]))
        material.extend(strings(q.get("assets", {}).get("preparation_resource", {}).get("learner_material", {})))
    for path in (ROOT / "apps/web/src/content").glob("fundamentals-*.json"):
        if path.name != "fundamentals-revisions.json":
            material.extend(strings(read(path)))
    for q in read(ROOT / "backend/seeds/duel_quiz.json")["questions"]:
        if q.get("source_key"):
            material.extend(strings({key: q[key] for key in ("prompt", "choices", "explanation")}))
    retired = re.compile(r"דלגלג|מרבב|נועל|\bpilot\b|פיילוט|hint queue|תור הרמזים|"
                         r"לפי בקשת הראל|לבקשת הראל|באישור הראל|requested by Harel|"
                         r"AI-assisted|בסיוע AI|professional review|expert review|human review|"
                         r"ביקורת (?:אנושית|מקצועית)|סקירה מקצועית", re.I)
    bad = []
    for value in material:
        prose = re.sub(r"```[\s\S]*?```", "", value)
        if match := retired.search(prose):
            bad.append(prose[max(0, match.start() - 25):match.end() + 75])
    assert not bad, bad


def test_verb_encoding_remains_a_verb_and_glossary_uses_local_component_names():
    quiz = read(ROOT / "backend/seeds/duel_quiz.json")["questions"]
    for q in quiz:
        if q.get("source_key") == "quick-sw-118":
            assert "האמירה מקודדת" in q["explanation"]["he"]
            assert "אנקודרת" not in q["explanation"]["he"]
    glossary = {q["key"]: q for q in read(ROOT / "backend/seeds/glossary.json")}
    for key, he in {"flip_flop": "פליפ-פלופ", "latch": "לאץ׳", "multiplexer": "מוקס",
                    "demultiplexer": "דה-מוקס", "decoder": "דקודר", "encoder": "אנקודר"}.items():
        assert glossary[key]["he"] == he and glossary[key]["keep_english"] is False
        assert not re.search(r"[\u0590-\u05ff]", glossary[key]["en"])
