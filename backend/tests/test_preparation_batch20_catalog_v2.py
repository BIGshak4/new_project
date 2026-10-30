"""Permanent publication/privacy contracts for the twenty-image October 25 batch.

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
NEW_IDS = {f"PREP-{number:03d}" for number in range(126, 137)}
SOURCE_MAP = {
    1: "PREP-126",
    2: "PREP-057",
    3: "PREP-127",
    4: "PREP-128",
    5: "PREP-058",
    6: "PREP-114",
    7: "PREP-129",
    8: "PREP-130",
    9: "PREP-045",
    10: "PREP-057",
    11: "PREP-031",
    12: "PREP-094",
    13: "PREP-041",
    14: "PREP-131",
    15: "PREP-098",
    16: "PREP-132",
    17: "PREP-133",
    18: "PREP-134",
    19: "PREP-135",
    20: "PREP-136",
}
SOURCE_ONLY_TECHNICAL_SHA256 = {
    "PREP-031": "28b67c5801bfb15be4a74a7aac3ce940601d5c6c18f92f653aa4e56a49face3d",
    "PREP-045": "d81f7c3cdd009388d8ac7d9dc199d9d5ec7743389f52e13a329ccdd6f507bd05",
    "PREP-058": "af3cd20db561491e85acd44400242f529b5b5a6669f59dcfbe11a05fc56494fd",
    "PREP-114": "21264a96df2abe13ec2d6f61642b0ccbaa57e073fde5a1d4536a5947d449c6fa",
}


@pytest.fixture
def catalog():
    return load_catalog(SEEDS)


def archive():
    return json.loads((BANK / "questions.json").read_text(encoding="utf-8"))


def test_ten_sources_have_exact_identity_mapping_and_permanent_matching_bytes():
    manifest = json.loads((BANK / "intakes/2026-10-25-batch20-sources.json").read_text(encoding="utf-8"))
    assert manifest["screenshot_count"] == len(manifest["sources"]) == 20
    assert {item["screenshot"] for item in manifest["sources"]} == set(SOURCE_MAP)
    all_questions = {item["id"]: item for item in archive()["questions"]}
    for source in manifest["sources"]:
        number = source["screenshot"]
        expected = SOURCE_MAP[number]
        assert source["question_ids"] == [expected]
        assert source["original_prompt"].strip()
        assert source["archive_paths"] == [f"sources/2026-10-25-batch20-{number:02d}.png"]
        path = source["archive_paths"][0]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source["sha256"]
        assert any(item.get("path") == path for item in all_questions[expected]["sources"])
        assert set(source["reported_companies"]) <= set(all_questions[expected]["reported_companies"])
        assert set(source["source_tags"]) <= set(all_questions[expected]["source_tags"])
    old_ids = set(SOURCE_MAP.values()) - NEW_IDS
    assert len(NEW_IDS) == 11 and len(old_ids) == 8
    assert old_ids == set(SOURCE_ONLY_TECHNICAL_SHA256) | {"PREP-041", "PREP-057", "PREP-094", "PREP-098"}


def test_source_only_questions_preserve_versions_translations_and_three_hint_sets():
    questions = {item["id"]: item for item in archive()["questions"]}
    for ident, expected_hash in SOURCE_ONLY_TECHNICAL_SHA256.items():
        question = questions[ident]
        technical = {key: question.get(key) for key in ("version", "translations", "prepared_hints")}
        serialized = json.dumps(technical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        assert hashlib.sha256(serialized.encode()).hexdigest() == expected_hash, ident


def test_eleven_new_questions_are_bilingual_pending_review_and_never_assessment_ready(catalog):
    assert len(archive()["questions"]) == 186
    assert len(catalog.questions) == 216
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
            if ident == "PREP-132":
                assert len(signed[-1]) == 1 and "rc-question-circuit" in signed[-1][0]["filename"]
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


PREFIX_BASELINES = {
    "PREP-041": {
        "old_version": 2,
        "languages": {
            "he": {
                "prompt": {
                    "length": 1129,
                    "sha256": "2dce6604a131f8b330c677d133a83bc2e6826d6885a180d900771cca3959d79b",
                },
                "reference_solution": {
                    "length": 9018,
                    "sha256": "2ffa5c80e1868f6f7054acf2d185180e4a62132eb2f1876a6b6db2bdc1064de7",
                },
                "hints": [
                    "אין צורך לשחזר את הסדר האקראי. איזה מידע אפשר לחשב מראש על כל המספרים בטווח, ואז להשוות למה שנותר?",
                    "ערך חסר אחד אפשר למצוא מהפרש הסכומים. כשחסרים שניים, הסכום נותן רק את החיבור שלהם. איזו פעולה מבטלת ערך שמופיע פעמיים?",
                    "בצעו XOR על הטווח המלא ועל המערך שנותר. התוצאה היא XOR של שני החסרים. מצאו בתוצאה ביט שערכו 1, חלקו לפי הביט הזה את שתי קבוצות הקלט, ובצעו XOR נפרד בכל צד.",
                ],
            },
            "en": {
                "prompt": {
                    "length": 1374,
                    "sha256": "c3ebdace901f1d49124389772417e257e570a3061a4dd091cc4cb5860af146cf",
                },
                "reference_solution": {
                    "length": 10792,
                    "sha256": "caf2fbc3ea6645dfeed5ef7d313a15132d738777902ecb7acc41193d02b18e18",
                },
                "hints": [
                    "You do not need to reconstruct the random order. What aggregate can you compute for the complete range and compare with the remaining entries?",
                    "A difference of sums finds one missing value. For two, it gives only their sum. Which operation cancels a value appearing twice?",
                    "XOR the complete range and the remaining entries. The result is the XOR of the two missing values. Choose a set bit in that result, partition both inputs by it, and XOR each group separately.",
                ],
            },
        },
    },
    "PREP-057": {
        "old_version": 1,
        "languages": {
            "he": {
                "prompt": {
                    "length": 938,
                    "sha256": "55d193a50c65e8dfa61027878da12be0b007722fa3fec03678690941ef868c8e",
                },
                "reference_solution": {
                    "length": 4046,
                    "sha256": "834a1e039ac85de4a24f150b17806af31d0ff7e483433c304ee4a1611c37091b",
                },
                "hints": [
                    "אין צורך שכל אסיר ידע מי כבר ביקר. אפשר למנות אסיר אחד שיאסוף סימנים מהאחרים, ולתת לכל אסיר מספר מוגבל של סימנים.",
                    "מתג האות יכול לייצג סימן אחד שממתין לאיסוף. רק הסופר יכבה אותו, והאחרים ידליקו רק כשהוא כבוי. חישבו איך מצב התחלתי דלוק יכול להיראות כמו סימן שלא נשלח.",
                    "אפשרו לכל אחד מ־20 האסירים האחרים לשלוח לכל היותר שני סימנים. כמה סימנים לכל היותר יוכל הסופר לאסוף אם אחד מהם עוד לא ביקר, כולל סימן התחלתי שגוי? בביקור שאין בו פעולת אות אפשר להשאיר את הנורה כפי שהיא.",
                ],
            },
            "en": {
                "prompt": {
                    "length": 1154,
                    "sha256": "3ab3229d5a7163dbc2f3fee8796ff38fac610dee4c4e04718be7116288a7283e",
                },
                "reference_solution": {
                    "length": 5006,
                    "sha256": "8f95184da2496ba7c4b2c1a63b1d4b5b4fe5b610ba9586c7f87a3f9840b0aa38",
                },
                "hints": [
                    "Not everyone needs to know who has visited. Designate one prisoner to collect signals and give every other prisoner a bounded allowance of signals.",
                    "The signal switch can store one pending token. Only the counter turns it OFF; contributors turn it ON only while it is OFF. How can an initially ON state masquerade as a token nobody sent?",
                    "Let each of the 20 contributors send at most two tokens. How many can the counter collect if one contributor has never visited, including one possible phantom initial token? A visit without a signal action may leave the light unchanged.",
                ],
            },
        },
    },
    "PREP-094": {
        "old_version": 1,
        "languages": {
            "he": {
                "prompt": {
                    "length": 425,
                    "sha256": "5387d3a7b51b6ffdc185a7967516da9b4351c877f26882c09da394d7aba1b8ba",
                },
                "reference_solution": {
                    "length": 2546,
                    "sha256": "205b5a09530fdd99c5aba1667933ac2713f6e0b727382146729a03f2fa83151e",
                },
                "hints": [
                    "הסיבית הימנית ביותר של הקלט צריכה להיות השמאלית ביותר בפלט. איך מבודדים אותה בפעולת ביטים?",
                    "התחילו מתוצאה אפס. הזיזו אותה שמאלה והוסיפו מימין את הסיבית שחילצתם; לאחר מכן הזיזו את הקלט ימינה.",
                    "בצעו בדיוק שמונה איטרציות: result=(result<<1)|(value&1), ואז value>>=1. אל תעצרו כאשר value נהיה אפס, כי עדיין ייתכנו אפסים מובילים שיש לעבד.",
                ],
            },
            "en": {
                "prompt": {
                    "length": 513,
                    "sha256": "6847105a0c2e6498cf0e0113f8757355a742cf8fc97f700c56106838799f2d36",
                },
                "reference_solution": {
                    "length": 3000,
                    "sha256": "e746bca57859d72efbfa49893626e2c3bc22cbb4f9f5e3545e47a33b6ffcc8ac",
                },
                "hints": [
                    "The input's rightmost bit must become the output's leftmost bit. How can a bitwise operation isolate it?",
                    "Start with result zero. Shift it left and append the extracted bit on the right; then shift the input right.",
                    "Run exactly eight iterations: result=(result<<1)|(value&1), then value>>=1. Do not stop when value becomes zero: fixed-width leading zeros still need processing.",
                ],
            },
        },
    },
    "PREP-098": {
        "old_version": 1,
        "languages": {
            "he": {
                "prompt": {
                    "length": 578,
                    "sha256": "a7a8e7adeb39bf1d60b3c51e30787d5c3439c2b2e7fc7741b17ae510b5be3116",
                },
                "reference_solution": {
                    "length": 3663,
                    "sha256": "a05406d9fb7d99a8e610f2cb65a94abccd756200345e8e65b7a749da56e91a04",
                },
                "hints": [
                    "האיבר הקטן ביותר שנותר בכל מערך נמצא בתחילת החלק שעוד לא קראנו. אילו שני איברים מספיק להשוות כדי לבחור את הבא בפלט?",
                    "החזיקו אינדקס נפרד לכל מערך. העתיקו את הקטן מבין שני האיברים הנוכחיים וקדמו רק את האינדקס שממנו הוא נלקח. בשוויון לא מוחקים אף מופע.",
                    "כל עוד לשניהם יש איבר משווים, ובשוויון בוחרים left. כשאחד נגמר, מעתיקים את כל מה שנותר בשני. כל צעד צורך מופע אחד בדיוק, ולכן נשמרים כל n+m האיברים.",
                ],
            },
            "en": {
                "prompt": {
                    "length": 725,
                    "sha256": "1c9848ac9d85354d50b4a843ef6b1ae494ca7d81cbe22a2ddb624de2a960ef58",
                },
                "reference_solution": {
                    "length": 4472,
                    "sha256": "ff4aa2387390217bb39c5cf561c367891b46810b032755f628e2ce222a1bc6f0",
                },
                "hints": [
                    "The smallest remaining item in either array is the first unread one. Which two items suffice to choose the next output item?",
                    "Keep a separate index for each array. Copy the smaller current value and advance only its input index. A tie must not discard either occurrence.",
                    "Compare while both have unread items, taking left on equality. Once one input ends, copy the other's remaining suffix. Each step consumes exactly one occurrence, preserving all n+m items.",
                ],
            },
        },
    },
}


def test_four_expanded_questions_keep_runtime_prefixes_hints_and_invalidate_whole_solution_attestation(
    catalog,
):
    for ident, baseline in PREFIX_BASELINES.items():
        question = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == ident)
        if ident in {"PREP-041", "PREP-094"}:
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


def test_c_mirror_is_a_hashed_private_solution_resource_and_not_a_raw_source(catalog):
    q = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == "PREP-094")
    media = [m for m in q.assets["bank_media"] if m["filename"].endswith(".c")]
    assert len(media) == 1
    item = media[0]
    assert item["role"] == "solution" and item["kind"] == "file"
    assert item["source_path"] == "solutions/prep_094_binary_mirror.c"
    data = (BANK / item["source_path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == item["sha256"]
    assert b"uint8_t" in data and b"0x55" in data
    for language in ("he", "en"):
        assert item in question_resources.learner_media(q.assets["bank_media"], language)
        assert item not in [
            m
            for m in question_resources.learner_media(q.assets["bank_media"], language)
            if m["role"] == "prompt"
        ]


def test_rc_question_has_a_clean_prompt_circuit_and_gates_the_solved_waveforms(catalog):
    q = next(q for q in catalog.questions.values() if q.assets.get("preparation_id") == "PREP-132")
    for language in ("he", "en"):
        media = question_resources.learner_media(q.assets["bank_media"], language)
        prompt = [m for m in media if m["role"] == "prompt"]
        assert len(prompt) == 1 and "rc-question-circuit" in prompt[0]["filename"]
        assert any("rc-ideal-waveforms" in m["filename"] and m["role"] == "solution" for m in media)
