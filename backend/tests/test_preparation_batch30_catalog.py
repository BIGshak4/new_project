"""Permanent publication/privacy contracts for the ten-source October 24 batch.

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
from tests.test_practice_hardening import scripted

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
NEW_IDS = {f"PREP-{number:03d}" for number in range(115, 121)}
SOURCE_MAP = {
    1: "PREP-115", 2: "PREP-116", 3: "PREP-117", 4: "PREP-118", 5: "PREP-119",
    6: "PREP-031", 7: "PREP-016", 8: "PREP-120", 9: "PREP-041", 10: "PREP-064",
}
SOURCE_ONLY_TECHNICAL_SHA256 = {"PREP-016": "f806c77eb28131be69c55469936464f88719760ebd5d8f21f4b6ad6e24edceeb"}


@pytest.fixture
def catalog():
    return load_catalog(SEEDS)


def archive():
    return json.loads((BANK / "questions.json").read_text(encoding="utf-8"))


def test_ten_sources_have_exact_identity_mapping_and_permanent_matching_bytes():
    manifest = json.loads((BANK / "intakes/2026-10-24-batch30-sources.json").read_text(encoding="utf-8"))
    assert manifest["screenshot_count"] == len(manifest["sources"]) == 10
    assert {item["screenshot"] for item in manifest["sources"]} == set(SOURCE_MAP)
    all_questions = {item["id"]: item for item in archive()["questions"]}
    for source in manifest["sources"]:
        number = source["screenshot"]
        expected = SOURCE_MAP[number]
        assert source["question_ids"] == [expected]
        assert source["original_prompt"].strip()
        assert source["archive_paths"] == [f"sources/2026-10-24-batch30-{number:02d}.png"]
        path = source["archive_paths"][0]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source["sha256"]
        assert any(item.get("path") == path for item in all_questions[expected]["sources"])
    old_ids = set(SOURCE_MAP.values()) - NEW_IDS
    assert len(NEW_IDS) == 6 and len(old_ids) == 4
    assert old_ids == set(SOURCE_ONLY_TECHNICAL_SHA256) | {"PREP-031", "PREP-041", "PREP-064"}


def test_source_only_questions_preserve_versions_translations_and_three_hint_sets():
    questions = {item["id"]: item for item in archive()["questions"]}
    for ident, expected_hash in SOURCE_ONLY_TECHNICAL_SHA256.items():
        question = questions[ident]
        technical = {key: question.get(key) for key in ("version", "translations", "prepared_hints")}
        serialized = json.dumps(technical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        assert hashlib.sha256(serialized.encode()).hexdigest() == expected_hash, ident


def test_six_new_questions_are_bilingual_pending_review_and_never_assessment_ready(catalog):
    assert len(archive()["questions"]) == 135
    assert len(catalog.questions) == 165
    additions = {q.assets.get("preparation_id"): q for q in catalog.questions.values()
                 if q.assets.get("preparation_id") in NEW_IDS}
    assert set(additions) == NEW_IDS
    required = {"assumptions", "optimality", "verification", "edge_cases", "common_mistakes",
                "interview_answer", "solution_extensions", "source_ambiguities"}
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
            assert not any("\u05d0" <= char <= "\u05ea"
                           for char in json.dumps(pair["en"], ensure_ascii=False)), (ident, field)
        for language in ("he", "en"):
            text = question.text(language)
            assert text.prompt and text.reference_solution
            assert len(text.hints) == len(set(text.hints)) == 3, (ident, language)
            assert not text.parity_checked
            if language == "en":
                assert not any("\u05d0" <= char <= "\u05ea"
                               for char in text.prompt + text.reference_solution + "".join(text.hints))
            public = summary(LoadedQuestion(uuid.uuid4(), question, question.version), language)
            assert public.preparation_id == ident
            assert public.difficulty is None and not public.assessment_ready and not public.reviewed
            assert text.reference_solution not in public.model_dump_json()
            assert not bank._servable(question, mode="deep", language=language,
                                      allow_in_review=True, require_parity=False)


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
            assert all(item["source_path"].startswith("diagrams/") and item.get("language") == language
                       for item in diagrams)


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
    assert len(questions) == 6
    for question in questions:
        ident = question.assets["preparation_id"]
        started = await service.start(user, question_key=question.key, mode="deep", language="he")
        attempt_id = uuid.UUID(started.id)
        for language in ("he", "en"):
            hidden = await service.question_resources(user, question.key, attempt_id=attempt_id, language=language)
            assert hidden.reference is None and hidden.technical_material is None and not hidden.solution_revealed
            assert all(item["role"] == "prompt" and item["source_path"].startswith("diagrams/")
                       and item.get("language") == language for item in signed[-1])
            assert signed[-1] == [], "new source-only prompts do not contain authored solution diagrams"
        with pytest.raises(ApiError) as denied:
            await service.question_resources(stranger, question.key, attempt_id=attempt_id)
        assert denied.value.code == "not_found"
        await service.reveal_reference(user, attempt_id)
        for language in ("he", "en"):
            revealed = await service.question_resources(user, question.key, attempt_id=attempt_id, language=language)
            assert revealed.solution_revealed and revealed.reference == question.text(language).reference_solution
            assert revealed.technical_material["id"] == ident
            assert revealed.solution_review.status == "pending_review"
            assert signed[-1] == question_resources.learner_media(question.assets["bank_media"], language)
            assert any(item["role"] == "solution" for item in signed[-1])
            assert all(not item["source_path"].startswith("sources/") for item in signed[-1])
        assert store.attempts[attempt_id]["row"]["practice_language"] == "he"
    assert not store.metrics


PREFIX_BASELINES = {'PREP-031': {'old_version': 1, 'languages': {'he': {'prompt': {'length': 216, 'sha256': '1364513af34069085321153d7606ea7b2e9c6a32030f5b83cc71a4fcffa94430'}, 'reference_solution': {'length': 2068, 'sha256': 'a9f6aa87dd2fd49c9fcf22a28d0be3224104a42a2a1c6a52b9663eedec4647b1'}, 'hints': ['כתוב מה הפלט צריך להיות כאשר אחת הכניסות היא 0 ומה הוא צריך להיות כאשר היא 1. זכור שלרשותך רק קבוע 0, בלי קבוע 1 או שער NOT.', 'אין צורך לייצר את השלילה של כניסה בכל המצבים: אפשר לייצר אות שמתנהג כמו השלילה רק כאשר המוקס הבא באמת בוחר בו.', 'בחר a כסלקטור של המוקס האחרון. כש־a=0 צריך להעביר b. כש־a=1 צריך להעביר NOT b: האם a עצמו יכול לשמש ערך 1 בענף הזה בלבד?']}, 'en': {'prompt': {'length': 250, 'sha256': '1c8e88c1e4e9efc8f8a3a5a58e779d0b64fbd65e75b176cd97c91e525b6fb350'}, 'reference_solution': {'length': 1322, 'sha256': '51d4b8028d3c08dfa6bb03cc6e713ef26bc70fc98d59fb1172216fd9e23e405c'}, 'hints': ['Condition on one input. Remember that only constant zero is allowed, with no constant one or NOT gate.', 'You need not produce a globally inverted signal: it only has to behave like an inverse in the branch where the next MUX selects it.', 'Use a as the final selector. When a=0, pass b. When a=1, you need NOT b: can a itself supply one inside that branch?']}}}, 'PREP-041': {'old_version': 1, 'languages': {'he': {'prompt': {'length': 602, 'sha256': '780896e653b1f780a28c8e5f798fa6353f1a9cf9b060cbe3945e09176a1192c3'}, 'reference_solution': {'length': 6123, 'sha256': '31da4dfc1baebdff488e3b05b12d52e871e955e3028f31a44482e8006b59fa59'}, 'hints': ['אין צורך לשחזר את הסדר האקראי. איזה מידע אפשר לחשב מראש על כל המספרים בטווח, ואז להשוות למה שנותר?', 'ערך חסר אחד אפשר למצוא מהפרש הסכומים. כשחסרים שניים, הסכום נותן רק את החיבור שלהם. איזו פעולה מבטלת ערך שמופיע פעמיים?', 'בצעו XOR על הטווח המלא ועל המערך שנותר. התוצאה היא XOR של שני החסרים. מצאו בתוצאה ביט שערכו 1, חלקו לפי הביט הזה את שתי קבוצות הקלט, ובצעו XOR נפרד בכל צד.']}, 'en': {'prompt': {'length': 698, 'sha256': 'a3163c4aebee3ce8f583a691a1464762db18f9c0e0d94d6fdf9f7ef089a29b9c'}, 'reference_solution': {'length': 7324, 'sha256': '4e98ff34b6349c642cec4b054e482123db520c368c5895b63f92ae4bcdce3ed9'}, 'hints': ['You do not need to reconstruct the random order. What aggregate can you compute for the complete range and compare with the remaining entries?', 'A difference of sums finds one missing value. For two, it gives only their sum. Which operation cancels a value appearing twice?', 'XOR the complete range and the remaining entries. The result is the XOR of the two missing values. Choose a set bit in that result, partition both inputs by it, and XOR each group separately.']}}}, 'PREP-064': {'old_version': 1, 'languages': {'he': {'prompt': {'length': 665, 'sha256': 'b4c8f3d7a4fa1a13f3112d38473b0c442cfdf8dfa97143fb9560b8492a015bc4'}, 'reference_solution': {'length': 3214, 'sha256': 'acc99c6e9d9dd41c7595a3d99aa53017ddb2caab8d6c27be94134f25c901d25f'}, 'hints': ['במקום לחשב סכום, בדקו אילו ביטים מתהפכים בכל הוספה או חיסור של אחד. מתי הביט הנמוך מתהפך?', 'בספירה למעלה ביט גבוה מתהפך כאשר כל הביטים שמתחתיו הם 1; בספירה למטה הוא מתהפך כשכולם 0. הפרידו בין פקודת עלייה בלבד לפקודת ירידה בלבד.', 'צרו U=inc AND NOT dec ו־D=dec AND NOT inc. הגדירו לכל ביט אות T שאומר אם להפוך אותו. כניסת דלגלג D יכולה להיות q XOR T; אות T הגבוה צריך לבדוק גם את q1 וגם את q0.']}, 'en': {'prompt': {'length': 742, 'sha256': '6619c4fc0a8606be657f34e1e6e900ca47be04d7962bb27ec77713499ed33657'}, 'reference_solution': {'length': 3432, 'sha256': 'd2ee188456443cea40eb04f5192d8f4364eb66c2c83c2bfdac688f7a061a125f'}, 'hints': ['Instead of calculating a sum, ask which bits toggle when adding or subtracting one. When does the lowest bit toggle?', 'Counting up toggles a higher bit when all lower bits are one; counting down toggles it when all lower bits are zero. Separate up-only from down-only commands.', 'Create U=inc AND NOT dec and D=dec AND NOT inc. Let each T signal indicate a bit toggle. A DFF input can be q XOR T; the highest toggle must test both q1 and q0.']}}}}


def test_three_expanded_questions_keep_runtime_prefixes_hints_and_invalidate_whole_solution_attestation(catalog):
    for ident, baseline in PREFIX_BASELINES.items():
        question = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == ident)
        assert question.version >= baseline["old_version"] + 1
        assert solution_review(question).status == "pending_review"
        for language, previous in baseline["languages"].items():
            current = question.text(language)
            assert list(current.hints) == previous["hints"]
            for field in ("prompt", "reference_solution"):
                value = getattr(current, field)
                expected = previous[field]
                assert len(value) > expected["length"]
                assert hashlib.sha256(value[:expected["length"]].encode()).hexdigest() == expected["sha256"], (ident, language, field)
