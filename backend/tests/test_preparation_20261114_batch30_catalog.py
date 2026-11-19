"""Keep the November 14 source identities, sharing and diagram roles traceable."""
import hashlib
import json
from pathlib import Path

from app.engine.question_difficulty import difficulty_fingerprint
from app.services.question_resources import learner_media

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"

# Two sources describe Fisher-Yates. The priority mask and list/Two Sum
# screenshots each link to two independently searchable existing identities.
SOURCE_MAP = (
    (312,), (116,), (42,), (90,), (138,), (320,), (14, 107), (321,), (322,), (131,),
    (323,), (326,), (313,), (22,), (314,), (22,), (324,), (315,), (327,), (328,),
    (301,), (36,), (316,), (325,), (317,), (318,), (187,), (319,), (329,), (32, 40),
)
NEW = {f"PREP-{number}" for number in range(312, 330)}
EXTENSIONS = {"PREP-131", "PREP-138"}


def read(path):
    return json.loads(path.read_bytes())


def test_sources_keep_private_bytes_company_provenance_and_exact_identities():
    batch = read(ARCHIVE / "intakes/2026-11-14-batch30-sources.json")
    by_id = {q["id"]: q for q in read(ARCHIVE / "questions.json")["questions"]}
    seen = set()
    assert batch["screenshot_count"] == batch["source_count"] == len(SOURCE_MAP)
    for number, (source, ids) in enumerate(zip(batch["sources"], SOURCE_MAP, strict=True), 1):
        assert source["screenshot"] == number and source["original_prompt"].strip()
        targets = [f"PREP-{value:03d}" for value in ids]
        assert source["question_ids"] == targets
        path = f"sources/2026-11-14-batch30-{number:02d}.png"
        assert source["archive_paths"] == [path]
        assert hashlib.sha256((ARCHIVE / path).read_bytes()).hexdigest() == source["sha256"]
        for ident in targets:
            record = by_id[ident]
            assert set(source["reported_companies"]) <= set(record["reported_companies"])
            assert any(item["path"] == path for item in record["sources"])
            decision = ("new_question" if ident in NEW else "technical_extension" if ident in EXTENSIONS
                        else "additional_source_existing_question")
            assert source["decision"] == decision
            seen.add(ident)
    assert batch["affected_question_count"] == len(seen) == 31
    assert (batch["new_question_count"], batch["technical_extension_count"], batch["provenance_only_count"]) == (18, 2, 11)
    # The shovel source has only tags. The DSP source names one company and tags another.
    assert by_id["PREP-312"]["reported_companies"] == []
    assert by_id["PREP-329"]["reported_companies"] == ["Mellanox"]


def test_published_questions_keep_ratings_and_bilingual_reveal_boundaries():
    by_id = {q["assets"]["preparation_id"]: q for q in read(SEEDS / "questions/preparation_bank.json")}
    ratings = read(SEEDS / "question_difficulty.json")
    for ident in NEW | EXTENSIONS:
        q = by_id[ident]
        assets = q["assets"]
        rating = ratings[q["key"]]
        assert type(rating["difficulty"]) is int and 1 <= rating["difficulty"] <= 10
        assert q["difficulty"] == rating["difficulty"] and rating["reason"].strip()
        assert assets["difficulty_status"] == "rated"
        assert rating["content_sha256"] == difficulty_fingerprint(q)
        assert q["status"] == "trial" and assets["assessment_ready"] is False
        for lang in ("en", "he"):
            text = q["translations"][lang]
            assert text["prompt"].strip() and text["reference_solution"].strip()
            assert len(text["hints"]) == len(set(text["hints"])) == 3
            media = learner_media(assets["bank_media"], lang)
            assert all(not item["source_path"].startswith("sources/") for item in media)
            if ident in {"PREP-312", "PREP-326", "PREP-327"}:
                for role in ("prompt", "solution"):
                    assert any(item.get("language") == lang and item["role"] == role and
                               item["source_path"].startswith("diagrams/") for item in media)

