"""Permanent publication/privacy contracts for the twenty-image October 30 batch.

No live credentials or database are used. Source-only records preserve the
pre-intake technical content; new material stays proposed and explicitly gated.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import pytest
from app.api.errors import ApiError
from app.engine import bank
from app.engine.catalog import load_catalog
from app.engine.solution_review import solution_review
from app.repo.questions import LoadedQuestion, summary
from app.services import question_resources
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig

from tests.preparation_history import before_batch20_record
from tests.test_practice_hardening import scripted

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
NEW_IDS = {f"PREP-{number:03d}" for number in range(137, 148)}
SOURCE_MAP = {1: 'PREP-023', 2: 'PREP-058', 3: 'PREP-043', 4: 'PREP-004', 5: 'PREP-137', 6: 'PREP-138', 7: 'PREP-139', 8: 'PREP-140', 9: 'PREP-141', 10: 'PREP-142', 11: 'PREP-143', 12: 'PREP-144', 13: 'PREP-145', 14: 'PREP-083', 15: 'PREP-146', 16: 'PREP-130', 17: 'PREP-077', 18: 'PREP-050', 19: 'PREP-147', 20: 'PREP-114'}
SOURCE_ONLY_TECHNICAL_SHA256 = {'PREP-023': '793dc9542c883f8310f79826c40725f70abaf367d443c06300d97ed328194f72', 'PREP-050': '0acf963c22ef39b3b91e1e5aac50bcbaafb71cffc92b12cd8acad26fda578976', 'PREP-058': 'af3cd20db561491e85acd44400242f529b5b5a6669f59dcfbe11a05fc56494fd', 'PREP-077': 'c1ed58b452a961eb251665fbcc55868b73086f8db752f4d8308263ac545ed0c5', 'PREP-083': '33d777510df846b1ecab98458efa153c5b4b4eacce6d431eccbe8aa07a81143a', 'PREP-114': '21264a96df2abe13ec2d6f61642b0ccbaa57e073fde5a1d4536a5947d449c6fa', 'PREP-130': 'dad3899932f54b2c8e873431443980061d9b9003669a33e368ed45a8d0596b85'}


@pytest.fixture
def catalog():
    return load_catalog(SEEDS)


def archive():
    return json.loads((BANK / "questions.json").read_text(encoding="utf-8"))


def test_ten_sources_have_exact_identity_mapping_and_permanent_matching_bytes():
    manifest = json.loads((BANK / "intakes/2026-10-30-batch20-sources.json").read_text(encoding="utf-8"))
    assert manifest["screenshot_count"] == len(manifest["sources"]) == 20
    assert {item["screenshot"] for item in manifest["sources"]} == set(SOURCE_MAP)
    all_questions = {item["id"]: item for item in archive()["questions"]}
    for source in manifest["sources"]:
        number = source["screenshot"]
        expected = SOURCE_MAP[number]
        assert source["question_ids"] == [expected]
        assert source["original_prompt"].strip()
        assert source["archive_paths"] == [f"sources/2026-10-30-batch20-{number:02d}.png"]
        path = source["archive_paths"][0]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source["sha256"]
        assert any(item.get("path") == path for item in all_questions[expected]["sources"])
        assert set(source["reported_companies"]) <= set(all_questions[expected]["reported_companies"])
        assert set(source["source_tags"]) <= set(all_questions[expected]["source_tags"])
    old_ids = set(SOURCE_MAP.values()) - NEW_IDS
    assert len(NEW_IDS) == 11 and len(old_ids) == 9
    assert old_ids == set(SOURCE_ONLY_TECHNICAL_SHA256) | {"PREP-004", "PREP-043"}


def test_source_only_questions_preserve_versions_translations_and_three_hint_sets():
    questions = {item["id"]: item for item in archive()["questions"]}
    for ident, expected_hash in SOURCE_ONLY_TECHNICAL_SHA256.items():
        question = before_batch20_record(questions[ident])
        technical = {key: question.get(key) for key in ("version", "translations", "prepared_hints")}
        serialized = json.dumps(technical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        assert hashlib.sha256(serialized.encode()).hexdigest() == expected_hash, ident


def test_eleven_new_questions_are_bilingual_pending_review_and_never_assessment_ready(catalog):
    assert len(archive()["questions"]) == 219
    assert len(catalog.questions) == 249
    additions = {
        q.assets.get("preparation_id"): q
        for q in catalog.questions.values()
        if q.assets.get("preparation_id") in NEW_IDS
    }
    assert set(additions) == NEW_IDS
    required = {
        "assumptions",
        "optimality",
        "verification",
        "edge_cases",
        "common_mistakes",
        "interview_answer",
        "solution_extensions",
        "source_ambiguities",
    }
    for ident, question in additions.items():
        assert question.status == "trial" and question.reuse_status == "pending_review", ident
        assert not question.reviewed_by and not question.assets["assessment_ready"], ident
        assert question.assets["difficulty_status"] == "unrated", ident
        assert solution_review(question).model_dump() == {"status": "pending_review", "reviewed_on": None}
        resource = question.assets["preparation_resource"]
        assert resource["solution_status"] == "proposed" and resource["ai_assisted"]
        material = resource["learner_material"]
        assert required <= material.keys(), ident
        for field, pair in material.items():
            assert set(pair) == {"he", "en"}, (ident, field)
            for language in ("he", "en"):
                assert pair[language] not in (None, "", [], {}), (ident, field, language)
            assert not any(
                "\u05d0" <= char <= "\u05ea" for char in json.dumps(pair["en"], ensure_ascii=False)
            ), (ident, field)
        for language in ("he", "en"):
            text = question.text(language)
            assert text.prompt and text.reference_solution
            assert len(text.hints) == len(set(text.hints)) == 3, (ident, language)
            assert not text.parity_checked
            if language == "en":
                assert not any(
                    "\u05d0" <= char <= "\u05ea"
                    for char in text.prompt + text.reference_solution + "".join(text.hints)
                )
            public = summary(LoadedQuestion(uuid.uuid4(), question, question.version), language)
            assert public.preparation_id == ident
            assert public.difficulty is None and not public.assessment_ready and not public.reviewed
            assert text.reference_solution not in public.model_dump_json()
            assert not bank._servable(
                question, mode="deep", language=language, allow_in_review=True, require_parity=False
            )


def test_every_new_private_media_path_matches_the_upload_manifest_and_learner_pngs_are_localized(catalog):
    uploads = json.loads((SEEDS / "preparation_uploads.json").read_text(encoding="utf-8"))["files"]
    manifest_entries = {entry["local_path"]: entry for entry in uploads.values()}
    for question in catalog.questions.values():
        ident = question.assets.get("preparation_id")
        if ident not in NEW_IDS:
            continue
        media = question.assets["bank_media"]
        assert any(item["source_path"].startswith("sources/") for item in media)
        for item in media:
            assert item["path"].startswith(ident.lower() + "/")
            assert question_resources.PATH.fullmatch(item["path"])
            entry = manifest_entries[item["source_path"]]
            digest = hashlib.sha256((BANK / item["source_path"]).read_bytes()).hexdigest()
            assert item["sha256"] == entry["sha256"] == digest
        for language in ("he", "en"):
            learner = question_resources.learner_media(media, language)
            assert learner
            assert all(not item["source_path"].startswith("sources/") for item in learner)
            diagrams = [item for item in learner if item["filename"].endswith(".png")]
            assert diagrams and any(item["role"] == "solution" for item in diagrams)
            assert all(
                item["source_path"].startswith("diagrams/") and item.get("language") == language
                for item in diagrams
            )


async def test_new_resources_require_owned_reveal_and_never_sign_archived_sources(catalog, monkeypatch):
    signed = []

    async def fake_sign(media, *_):
        signed.append(media)
        return []

    monkeypatch.setattr(question_resources, "sign_media", fake_sign)
    store = InMemoryStore(catalog)
    service = PracticeService(store, catalog, scripted([]), ServiceConfig())
    user, stranger = uuid.uuid4(), uuid.uuid4()
    questions = [q for q in catalog.questions.values() if q.assets.get("preparation_id") in NEW_IDS]
    assert len(questions) == 11
    for question in questions:
        ident = question.assets["preparation_id"]
        started = await service.start(user, question_key=question.key, mode="deep", language="he")
        attempt_id = uuid.UUID(started.id)
        for language in ("he", "en"):
            hidden = await service.question_resources(
                user, question.key, attempt_id=attempt_id, language=language
            )
            assert (
                hidden.reference is None
                and hidden.technical_material is None
                and not hidden.solution_revealed
            )
            assert all(
                item["role"] == "prompt"
                and item["source_path"].startswith("diagrams/")
                and item.get("language") == language
                for item in signed[-1]
            )
            if ident in {"PREP-140", "PREP-141", "PREP-147"}:
                assert len(signed[-1]) == 1 and signed[-1][0]["role"] == "prompt"
            else:
                assert signed[-1] == [], "solution diagrams must stay hidden before reveal"
        with pytest.raises(ApiError) as denied:
            await service.question_resources(stranger, question.key, attempt_id=attempt_id)
        assert denied.value.code == "not_found"
        await service.reveal_reference(user, attempt_id)
        for language in ("he", "en"):
            revealed = await service.question_resources(
                user, question.key, attempt_id=attempt_id, language=language
            )
            assert (
                revealed.solution_revealed
                and revealed.reference == question.text(language).reference_solution
            )
            assert revealed.technical_material["id"] == ident
            assert revealed.solution_review.status == "pending_review"
            assert signed[-1] == question_resources.learner_media(question.assets["bank_media"], language)
            assert any(item["role"] == "solution" for item in signed[-1])
            assert all(not item["source_path"].startswith("sources/") for item in signed[-1])
        assert store.attempts[attempt_id]["row"]["practice_language"] == "he"
    assert not store.metrics


PREFIX_BASELINES = {'PREP-004': {'old_version': 1, 'languages': {'he': {'prompt': {'length': 459, 'sha256': 'df4d6de4293d4cc5a9b9270414fcde8a46cff46368376a5482e810783f61b5d3'}, 'reference_solution': {'length': 816, 'sha256': '7b94ba018822b5a2ff238f5457b35929862e5ddb70a0787ce6806b091c533a8a'}, 'hints': ['הסתכל על שני הפולסים של out: מה קרה ל־In לפני כל אחד מהם, ומתי בדיוק out מגיב ביחס לחזיתות השעון? שים לב גם למשך של כל פולס.', 'בכל חזית עלייה השווה את הערך הנוכחי של In לערך שנדגם בחזית הקודמת. מה צריך לקרות בפלט כשהם שונים, ומה כשהם זהים? כדי לבצע את ההשוואה תצטרך לזכור את הדגימה הקודמת.', 'כתוב טבלת אמת עבור זוג הדגימות: 00 ו־11 פירושם שלא היה שינוי, ואילו 01 ו־10 פירושם שהיה שינוי. איזה שער מזהה בדיוק את המצבים האלה? כעת חשוב איך לשמור את תוצאת ההשוואה באוגר שמתעדכן בחזית עלייה, ובמקביל לעדכן את אוגר הדגימה הקודמת, כך ש־out יישאר יציב בין חזיתות.']}, 'en': {'prompt': {'length': 487, 'sha256': '5b34f31860f35f00a00d35e3ee1c1148c25847645e5115991f144debf13789a2'}, 'reference_solution': {'length': 1043, 'sha256': 'd0ca2e8b2d826debd7412d0962518373130bb8ef1952cee8ac2810d6704ae01b'}, 'hints': ['Look at the two output pulses: what happened to In before each pulse, when does out respond relative to clock edges, and how long does it stay high?', 'At each rising edge, compare the current input with the previous sampled input. What output is needed when they differ? You will need to remember the previous sample.', 'Make a truth table for the sample pair: 00 and 11 mean no change; 01 and 10 mean change. Which gate detects this? Consider registering the comparison while updating the previous sample so the output stays stable between edges.']}}}, 'PREP-043': {'old_version': 1, 'languages': {'he': {'prompt': {'length': 686, 'sha256': '4d1a4db9d0e1ab403f6ba06ea41868c8557cc56cffa3901d5c07fcff10bdf536'}, 'reference_solution': {'length': 7313, 'sha256': 'd27063a027d25f663767eb887757607c84fd9365b7311f8bf13c91af8b75ecc9'}, 'hints': ['חשבו איזה חלק מסוף הקלט שכבר הגיע עדיין יכול להיות התחלה של ABCD. האם צריך לזכור את כל התווים, או רק את מידת ההתקדמות ברצף?', 'נסו מצבים עבור אין התאמה, A, AB ו־ABC. תכננו גם מה קורה כשמגיע A במקום התו הבא שציפיתם לו; בדקו את ABCABCD.', 'רק D במצב שמייצג ABC משלים זיהוי. תו A מעביר תמיד למצב של A; שאר אי־ההתאמות מאפסות את ההתקדמות. לאחר מכן החליטו אם פלט הזיהוי הוא פעימה או מעבר למצב OPEN שנשמר עד איפוס.']}, 'en': {'prompt': {'length': 975, 'sha256': 'dc571de587472f7c39c527e34095a8043c43df6942055150b3d7e077f64c0eb3'}, 'reference_solution': {'length': 8667, 'sha256': '97db982df27273c43fa1c098c9dcc72f943314097d1a6eb46cc6b18067feef7d'}, 'hints': ['Which suffix of the input already consumed could still be the beginning of ABCD? Do you need the full history or only the progress through the target pattern?', 'Try states for no match, A, AB, and ABC. Work out what happens when A arrives instead of the expected next symbol; test ABCABCD.', 'Only D from the state representing ABC completes a match. A always leads to the A state, while other mismatches clear progress. Then choose between a detection pulse and an OPEN state held until reset.']}}}}


def test_two_expanded_questions_keep_runtime_prefixes_hints_and_invalidate_whole_solution_attestation(
    catalog,
):
    for ident, baseline in PREFIX_BASELINES.items():
        question = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == ident)
        assert question.version == baseline["old_version"] + 1
        assert solution_review(question).status == "pending_review"
        for language, previous in baseline["languages"].items():
            current = question.text(language)
            assert list(current.hints) == previous["hints"]
            for field in ("prompt", "reference_solution"):
                value = getattr(current, field)
                expected = previous[field]
                assert len(value) > expected["length"]
                assert (
                    hashlib.sha256(value[: expected["length"]].encode()).hexdigest() == expected["sha256"]
                ), (ident, language, field)
