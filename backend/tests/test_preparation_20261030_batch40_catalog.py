"""Permanent publication/privacy contracts for the second twenty-image October 30 batch.

No live credentials or database are used. Source-only records preserve the
pre-intake technical content; new material stays proposed and explicitly gated.
"""

from __future__ import annotations

import copy
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
from tests.preparation_history import assert_pre_batch90_assets
from tests.test_practice_hardening import scripted

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
NEW_IDS = {f"PREP-{number:03d}" for number in range(148, 160)}
SOURCE_MAP = {1: 'PREP-152', 2: 'PREP-112', 3: 'PREP-041', 4: 'PREP-158', 5: 'PREP-120', 6: 'PREP-155', 7: 'PREP-156', 8: 'PREP-155', 9: 'PREP-148', 10: 'PREP-149', 11: 'PREP-059', 12: 'PREP-159', 13: 'PREP-153', 14: 'PREP-150', 15: 'PREP-009', 16: 'PREP-094', 17: 'PREP-151', 18: 'PREP-157', 19: 'PREP-154', 20: 'PREP-096'}
SOURCE_ONLY_TECHNICAL_SHA256 = {'PREP-041': '00af53562df488ec068c9d5600036b1c4ff3fe9bc6f7d9279949ba9dc7f79c5b', 'PREP-112': '679a4597d2ccb61e12888c7e7d4383c73108d14a26992f002af3489cd4d64a58', 'PREP-120': '46a1c3301169a4bdf41c43ef3a8f066967b1d00f27a8190b39287be4acd88a13'}


# A later intake appends a one-pass variant. Rebuild the earlier snapshot
# before checking its original unchanged SHA256; hints/titles remain exact.
LATER_PREP041_PREFIX = {'version': 3, 'he': {'prompt': 1724, 'reference_solution': 12557}, 'en': {'prompt': 2129, 'reference_solution': 14630}}


@pytest.fixture
def catalog():
    return load_catalog(SEEDS)


def archive():
    return json.loads((BANK / "questions.json").read_text(encoding="utf-8"))


def test_twenty_sources_have_exact_identity_mapping_and_permanent_matching_bytes():
    manifest = json.loads((BANK / "intakes/2026-10-30-batch40-sources.json").read_text(encoding="utf-8"))
    assert manifest["screenshot_count"] == len(manifest["sources"]) == 20
    assert {item["screenshot"] for item in manifest["sources"]} == set(SOURCE_MAP)
    all_questions = {item["id"]: item for item in archive()["questions"]}
    for source in manifest["sources"]:
        number = source["screenshot"]
        expected = SOURCE_MAP[number]
        assert source["question_ids"] == [expected]
        assert source["original_prompt"].strip()
        assert source["archive_paths"] == [f"sources/2026-10-30-batch40-{number:02d}.png"]
        path = source["archive_paths"][0]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source["sha256"]
        assert any(item.get("path") == path for item in all_questions[expected]["sources"])
        assert set(source["reported_companies"]) <= set(all_questions[expected]["reported_companies"])
        assert set(source["source_tags"]) <= set(all_questions[expected]["source_tags"])
    old_ids = set(SOURCE_MAP.values()) - NEW_IDS
    assert len(NEW_IDS) == 12 and len(old_ids) == 7
    assert old_ids == set(SOURCE_ONLY_TECHNICAL_SHA256) | {"PREP-009", "PREP-059", "PREP-094", "PREP-096"}


def test_source_only_questions_preserve_versions_translations_and_three_hint_sets():
    questions = {item["id"]: item for item in archive()["questions"]}
    for ident, expected_hash in SOURCE_ONLY_TECHNICAL_SHA256.items():
        question = questions[ident]
        technical = copy.deepcopy({key: question.get(key) for key in ("version", "translations", "prepared_hints")})
        if ident == "PREP-041":
            technical["version"] = LATER_PREP041_PREFIX["version"]
            assert question["version"] > technical["version"]
            for language in ("he", "en"):
                for field, length in LATER_PREP041_PREFIX[language].items():
                    technical["translations"][language][field] = technical["translations"][language][field][:length]
        serialized = json.dumps(technical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        assert hashlib.sha256(serialized.encode()).hexdigest() == expected_hash, ident


def test_twelve_new_questions_are_bilingual_pending_review_and_never_assessment_ready(catalog):
    assert len(archive()["questions"]) == 197
    assert len(catalog.questions) == 227
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
    assert len(questions) == 12
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
            if ident == "PREP-154":
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


PREFIX_BASELINES = {'PREP-009': {'old_version': 1, 'languages': {'he': {'prompt': {'length': 226, 'sha256': '6dc1d8937d9c0afa9acb104bfe70134168a5966a526e2348427c42a97afd8bde'}, 'reference_solution': {'length': 2139, 'sha256': '227cf2adf542c9f11ad80d71ed9994b8d7167fac4af59a5485a5540a7caf1eea'}, 'hints': ['חלק את הסוסים לקבוצות של חמישה והריץ כל קבוצה. חשוב מה סדר ההגעה מלמד אותך בתוך כל קבוצה, ומה עדיין אינך יודע על סוסים מקבוצות שונות.', 'אחרי המירוצים הראשונים, השווה בין מנצחי הקבוצות. כלל שימושי: אם אתה יודע ששלושה סוסים מהירים מסוס מסוים, הוא כבר לא יכול להיות בשלישייה הראשונה.', 'סמן את הקבוצות A עד E לפי סדר ההגעה של המנצחים. מהקבוצה A עדיין מעניינים שלושת הראשונים, מ־B שני הראשונים ומ־C הראשון. אחד מהם כבר מובטח במקום הראשון — כמה מועמדים נשארו לשני המקומות האחרים?']}, 'en': {'prompt': {'length': 256, 'sha256': '1ebd0dace813eda97ca3423c1ec770fcbe1c838a9e2976e50c40d8860233efbe'}, 'reference_solution': {'length': 1373, 'sha256': 'ed244bb0af8d514372544df98279da524bae777dcaa8625cd8529ece5ae37c56'}, 'hints': ['Race five groups of five. What ordering is known within each group, and what is still unknown between groups?', 'Compare the group winners. Any horse known to have at least three faster horses cannot finish in the top three.', "Name the groups A through E by the winners' finishing order. Retain the first three in A, first two in B and first in C. One horse is already the overall winner; how many candidates remain for the other places?"]}}}, 'PREP-059': {'old_version': 1, 'languages': {'he': {'prompt': {'length': 513, 'sha256': '56ce63f6cfb958226ddfdf11f816c2ce2bd5ae7d94d97df8c6e9ced4cc73c102'}, 'reference_solution': {'length': 1729, 'sha256': '56a8863c29e21f5f30416f8c34f0a9a8823f6eb35952bbfb375090b322389a4b'}, 'hints': ['אין צורך לדעת אילו מטבעות הם פלי. נסו לבחור קבוצה בגודל שקשור למספר הפלי הכולל הידוע.', 'אם בחרתם 10 מטבעות ומתוכם x הם פלי, כמה פלי נשארו בקבוצה האחרת וכמה עץ יש בקבוצה שנבחרה?', 'הפכו את כל 10 המטבעות בקבוצה שנבחרה בלבד. מספר הפלי החדש בה שווה למספר העץ שהיה בה קודם.']}, 'en': {'prompt': {'length': 567, 'sha256': 'e7581416687fcaf171e6165bdb2a4cbf86a969ea4deba2c7814109dff8bc7b6a'}, 'reference_solution': {'length': 2054, 'sha256': '34e2505fd088444f59f14364a06753531d79e10c3bf53062c03189a804feb9e5'}, 'hints': ['You need not identify the tails. Choose a group whose size is related to the known total tails count.', 'If you select ten coins and x of them are tails, how many tails remain outside, and how many heads are in the selected group?', 'Flip every selected coin and none of the rest. The selected group’s new tails count equals its previous heads count.']}}}, 'PREP-094': {'old_version': 2, 'languages': {'he': {'prompt': {'length': 911, 'sha256': 'bf1d78e1810e746307ab5b4a4a8a486ffd33c4171f9369a49ea67e5eab931270'}, 'reference_solution': {'length': 4892, 'sha256': 'c6db837695837a0456d70e472a9ecd6fb7c179783b65dd18d80843437ce628e1'}, 'hints': ['הסיבית הימנית ביותר של הקלט צריכה להיות השמאלית ביותר בפלט. איך מבודדים אותה בפעולת ביטים?', 'התחילו מתוצאה אפס. הזיזו אותה שמאלה והוסיפו מימין את הסיבית שחילצתם; לאחר מכן הזיזו את הקלט ימינה.', 'בצעו בדיוק שמונה איטרציות: result=(result<<1)|(value&1), ואז value>>=1. אל תעצרו כאשר value נהיה אפס, כי עדיין ייתכנו אפסים מובילים שיש לעבד.']}, 'en': {'prompt': {'length': 1084, 'sha256': 'a7fc2ee58a640e6ef4f38a8fb699352a22f46d98b9bf0ba10e8a66caf1722130'}, 'reference_solution': {'length': 5639, 'sha256': '2ec5a6ed92215fecb2718381acb6b23fa9f4e1b0e27f7ec3b6bb1981615c0472'}, 'hints': ["The input's rightmost bit must become the output's leftmost bit. How can a bitwise operation isolate it?", 'Start with result zero. Shift it left and append the extracted bit on the right; then shift the input right.', 'Run exactly eight iterations: result=(result<<1)|(value&1), then value>>=1. Do not stop when value becomes zero: fixed-width leading zeros still need processing.']}}}, 'PREP-096': {'old_version': 1, 'languages': {'he': {'prompt': {'length': 764, 'sha256': 'd19469321898ae6343f6a2bd8769b651852d3c205d557b1efc465e2af10f917b'}, 'reference_solution': {'length': 3440, 'sha256': 'a1776b1200d29d2e67a565018a0428c130e52415e19898307af3a50ac018f0ae'}, 'hints': ['האם הגמד הראשון יכול לנצל את מילת הצבע שלו כדי למסור מידע שימושי על כל הכובעים שהוא רואה, גם בלי לדעת את צבעו?', 'שתי מילים מספיקות להבדיל בין מספר זוגי למספר אי־זוגי של כובעים שחורים. מה הגמד הבא רואה לעומת מה שהראשון ראה?', 'שלבו את הזוגיות שהוכרזה עם הצבעים הנכונים שכבר נאמרו ועם הכובעים שעוד רואים. בכל שלב חסר ביט צבע אחד בלבד.']}, 'en': {'prompt': {'length': 966, 'sha256': '3ab0ce523cc325e939645960c8ba4e86687e451861214a2d4e0b0d9a2f91741b'}, 'reference_solution': {'length': 4226, 'sha256': '4cf745ea9e52c0e831132256faa42dad56f65268900d156fc26d187b1e793ef6'}, 'hints': ['Can the first dwarf use their color word to communicate something useful about all visible hats, without knowing their own?', 'Two words distinguish even from odd black-hat count. Which hat is missing from the next dwarf’s view compared with the first speaker’s?', 'Combine the announced parity, correct colors already heard and hats still visible. At each step exactly one color bit remains unknown.']}}}}


def test_four_expanded_questions_keep_runtime_prefixes_hints_and_invalidate_whole_solution_attestation(
    catalog,
):
    for ident, baseline in PREFIX_BASELINES.items():
        question = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == ident)
        if ident == "PREP-096":
            # The later thousand-person appendix must keep this batch's exact prefix.
            assert question.version >= baseline["old_version"] + 1
        else:
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


def test_batch40_inventory_retains_source_bytes_and_does_not_alias_new_variations():
    uploads = json.loads((SEEDS / "preparation_uploads.json").read_bytes())["files"]
    sources = [value["local_path"] for value in uploads.values() if value["local_path"].startswith("sources/")]
    assert_pre_batch90_assets(uploads)
    assert len(uploads) > 921
    assert len(sources) == 311 and len(set(sources)) == 310
    source_names = json.loads((ROOT / "apps/web/src/lib/source-screenshots.json").read_bytes())
    assert set(source_names) == {Path(path).name for path in sources}
    assert all(f"2026-10-30-batch40-{i:02d}.png" in source_names for i in range(1, 21))
    manifest = json.loads((BANK / "intakes/2026-10-30-batch40-sources.json").read_bytes())
    assert sum(item["question_ids"] == ["PREP-155"] for item in manifest["sources"]) == 2
    assert manifest["existing_content_revisions"] == ["PREP-009", "PREP-059", "PREP-094", "PREP-096"]
