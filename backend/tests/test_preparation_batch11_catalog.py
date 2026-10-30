"""Permanent publication/privacy contracts for the eleven-image October 25 batch.

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
from tests.preparation_history import BATCH110_BASELINE, before_batch110_record
from tests.test_practice_hardening import scripted

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
NEW_IDS = {f"PREP-{number:03d}" for number in range(121, 126)}
SOURCE_MAP = {
    1: "PREP-102", 2: "PREP-001", 3: "PREP-019", 4: "PREP-036", 5: "PREP-121",
    6: "PREP-023", 7: "PREP-122", 8: "PREP-123", 9: "PREP-124", 10: "PREP-125", 11: "PREP-125",
}
SOURCE_ONLY_TECHNICAL_SHA256 = {'PREP-023': '793dc9542c883f8310f79826c40725f70abaf367d443c06300d97ed328194f72', 'PREP-036': 'b824fc51e2b5908b34a92f49a9ec275443b456144a498a433b24c2a4d2dd8584', 'PREP-102': 'e55bfe57090cafc62ba32a86e246a66e7b31d58eea02208dd6865f0049da0560'}


@pytest.fixture
def catalog():
    return load_catalog(SEEDS)


def archive():
    return json.loads((BANK / "questions.json").read_text(encoding="utf-8"))


def test_ten_sources_have_exact_identity_mapping_and_permanent_matching_bytes():
    manifest = json.loads((BANK / "intakes/2026-10-25-batch11-sources.json").read_text(encoding="utf-8"))
    assert manifest["screenshot_count"] == len(manifest["sources"]) == 11
    assert {item["screenshot"] for item in manifest["sources"]} == set(SOURCE_MAP)
    all_questions = {item["id"]: item for item in archive()["questions"]}
    for source in manifest["sources"]:
        number = source["screenshot"]
        expected = SOURCE_MAP[number]
        assert source["question_ids"] == [expected]
        assert source["original_prompt"].strip()
        assert source["archive_paths"] == [f"sources/2026-10-25-batch11-{number:02d}.png"]
        path = source["archive_paths"][0]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source["sha256"]
        assert any(item.get("path") == path for item in all_questions[expected]["sources"])
    old_ids = set(SOURCE_MAP.values()) - NEW_IDS
    assert len(NEW_IDS) == 5 and len(old_ids) == 5
    assert old_ids == set(SOURCE_ONLY_TECHNICAL_SHA256) | {"PREP-001", "PREP-019"}


def test_source_only_questions_preserve_versions_translations_and_three_hint_sets():
    questions = {item["id"]: item for item in archive()["questions"]}
    for ident, expected_hash in SOURCE_ONLY_TECHNICAL_SHA256.items():
        question = questions[ident]
        technical = {key: question.get(key) for key in ("version", "translations", "prepared_hints")}
        serialized = json.dumps(technical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        assert hashlib.sha256(serialized.encode()).hexdigest() == expected_hash, ident


def test_five_new_questions_are_bilingual_pending_review_and_never_assessment_ready(catalog):
    assert len(archive()["questions"]) == 197
    assert len(catalog.questions) == 227
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
    assert len(questions) == 5
    for question in questions:
        ident = question.assets["preparation_id"]
        started = await service.start(user, question_key=question.key, mode="deep", language="he")
        attempt_id = uuid.UUID(started.id)
        for language in ("he", "en"):
            hidden = await service.question_resources(user, question.key, attempt_id=attempt_id, language=language)
            assert hidden.reference is None and hidden.technical_material is None and not hidden.solution_revealed
            assert all(item["role"] == "prompt" and item["source_path"].startswith("diagrams/")
                       and item.get("language") == language for item in signed[-1])
            if ident == "PREP-125":
                assert len(signed[-1]) == 1 and "primitive-register-instructions" in signed[-1][0]["filename"]
            else:
                assert signed[-1] == [], "solution diagrams must stay hidden before reveal"
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


PREFIX_BASELINES = {'PREP-001': {'old_version': 1, 'languages': {'he': {'prompt': {'length': 177, 'sha256': '3f7ba7896ab1f40b81df478c54e12dc29d166a252d10547148e624dc8144abe3'}, 'reference_solution': {'length': 3037, 'sha256': 'e7f2c69519781f0516ce3fdae0bbe6e5b4c64223ef67dabf3df09b213b7c5df3'}, 'hints': ['מה טווח מספר האחדות האפשרי, וכמה ביטים דרושים לפלט?', 'Full-Adder שומר על המשקל לפי a+b+c=S+2C. אילו אותות מותר לחבר יחד?', 'צמצמו קודם את עמודת משקל 1, העבירו נשאים לעמודת משקל 2 והמשיכו. בדקו גם את הקלט שבו כל הביטים הם 1.']}, 'en': {'prompt': {'length': 227, 'sha256': '38a4a9a709db776afaeaaddac658d071844dc3531be292e489cc1c681f5dbb89'}, 'reference_solution': {'length': 2843, 'sha256': '9a3276b5ec19546a10f0efce00a66a6d2e8009d05a9a4f8fe73ae3cfae031bd2'}, 'hints': ['Consider the possible count range and the width required for the output.', 'A full adder conserves weight: a+b+c=S+2C. Group only signals of equal weight.', 'Reduce the weight-one column first, pass carries to weight two, and repeat for higher columns. Check the all-ones input.']}}}, 'PREP-019': {'old_version': 1, 'languages': {'he': {'prompt': {'length': 327, 'sha256': 'fccaaf96963f4ea2e2ebf9d4497b379f794c8a7a4d03107e9d67f9c4a6a7a0c1'}, 'reference_solution': {'length': 3151, 'sha256': 'de0ff2fe4fc5158b14fef2c21ebebc50dd455f8ff51833b786de44855ed5db5d'}, 'hints': ['לא צריך למיין לפי השוואות בין כל זוג כדורים. יש רק שלוש קבוצות, והסדר בתוך כל צבע אינו חשוב. אילו צבעים אפשר להעביר מיד לקצוות?', 'נסה להחזיק גבול לאזור הכחול משמאל, גבול לאזור האדום מימין ואינדקס שסורק את האזור שטרם סווג. חשוב איזה אזור כבר ידוע כירוק.', 'כחול מעבירים לגבול השמאלי, ירוק משאירים ומתקדמים, ואדום מחליפים עם סוף האזור הלא מסווג. אחרי החלפה עם הצד הימני, האם כבר ידוע הצבע של הכדור שהגיע למיקום הסריקה?']}, 'en': {'prompt': {'length': 387, 'sha256': '9bb7cb67211b9bc6d46a415c0e41d36791bb532acc66ec4558bf62730838be18'}, 'reference_solution': {'length': 1402, 'sha256': 'aaf7cf317bf37c864ca21d97831eb68aaec8c421e3228e57c9f0da141d8c29d2'}, 'hints': ['There are only three groups, and within-color order is irrelevant. Which colors can be moved immediately to the ends?', 'Maintain a left boundary for blue, a right boundary for red, and a scanning index for the unclassified region. Which region is already known to be green?', 'Move blue to the left boundary, advance past green, and swap red with the end of the unclassified region. After a right-side swap, do you know the color that just arrived at the scanning index?']}}}}


def test_two_expanded_questions_keep_runtime_prefixes_hints_and_invalidate_whole_solution_attestation(catalog):
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
                assert hashlib.sha256(value[:expected["length"]].encode()).hexdigest() == expected["sha256"], (ident, language, field)


def test_primitive_isa_includes_both_native_programs_as_hashed_solution_files(catalog):
    q = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == "PREP-125")
    media = q.assets["bank_media"]
    programs = [m for m in media if m["filename"].endswith(".asm") and m["path"] in BATCH110_BASELINE["asset_sha256"]]
    assert {m["filename"] for m in programs} == {
        "prep_125_primitive_multiply.asm", "prep_125_primitive_absolute_difference.asm"}
    assert {m["filename"] for m in media if m["filename"].endswith(".asm")} == {
        *(m["filename"] for m in programs), "prep_125_eight_register_product_batch110.asm"}
    for m in programs:
        assert m["role"] == "solution" and m["kind"] == "file"
        data = (BANK / m["source_path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == m["sha256"]
        for line in data.decode().splitlines():
            instruction = line.split(";", 1)[0].strip()
            if instruction and not instruction.endswith(":"):
                assert instruction.split()[0].lower() in {"inc", "dec", "jnz", "halt"}
    for language in ("he", "en"):
        exposed = [m for m in question_resources.learner_media(media, language) if m["role"] == "prompt"]
        assert len(exposed) == 1 and exposed[0]["role"] == "prompt"
        assert not any(m["filename"].endswith(".asm") for m in exposed)
        for program in programs:
            assert (BANK / program["source_path"]).read_text().rstrip() in q.text(language).reference_solution


def test_assembly_question_does_not_invent_a_source_company_or_publish_personal_filename(catalog):
    q = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == "PREP-125")
    resource = q.assets["preparation_resource"]
    original = before_batch110_record(next(row for row in archive()["questions"] if row["id"] == "PREP-125"))
    assert not original["reported_companies"]
    intake = json.loads((BANK / "intakes/2026-10-30-batch110-sources.json").read_bytes())
    source = next(item for item in intake["sources"] if item["screenshot"] == 4)
    assert resource["reported_companies"] == source["reported_companies"] == ["Amazon"]
    media = q.assets["bank_media"]
    assert all("asm_" not in m["filename"] and "moshe" not in m["filename"].lower() for m in media)
    filenames = [m["filename"] for m in media if m["path"] in BATCH110_BASELINE["asset_sha256"]]
    assert all("primitive" in name or name.startswith("2026-10-25-batch11-") for name in filenames)
