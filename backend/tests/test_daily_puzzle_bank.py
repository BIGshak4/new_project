import hashlib
import json
from datetime import date, timedelta
from itertools import pairwise
from pathlib import Path

import pytest

from app.engine.catalog import load_catalog
from app.services.daily_puzzle import DailyPuzzleService
from app.services.daily_puzzle_bank import load_daily_bank

SEEDS = Path(__file__).resolve().parents[1] / "seeds"


@pytest.fixture(scope="module")
def interview_catalog():
    return load_catalog(SEEDS)


def test_every_daily_puzzle_has_its_own_bilingual_question_and_answer(interview_catalog):
    bank = load_daily_bank(interview_catalog, SEEDS)
    assert len(bank) == 200
    assert len({p.source_question_key for p in bank}) == 122
    for entry in bank:
        source = interview_catalog.questions[entry.source_question_key]
        for lang in ("he", "en"):
            assert entry.prompt[lang] != source.text(lang).prompt
            assert entry.solution[lang] != source.text(lang).reference_solution
            assert "sources/prep-" not in entry.prompt[lang] + entry.solution[lang]
            assert entry.title[lang] and entry.prompt[lang] and entry.solution[lang]
    sample = next(entry for entry in bank if entry.id == "coins-in-the-dark")
    assert "30" in sample.prompt["he"] and "Thirty" in sample.prompt["en"]
    assert all("3-k" in sample.solution[lang] for lang in ("he", "en"))


def test_expanded_pool_retains_launch_day_and_reaches_every_bilingual_variant(interview_catalog):
    bank = load_daily_bank(interview_catalog, SEEDS)
    game = DailyPuzzleService(lambda: bank)
    launch = date(2026, 11, 15)
    assert game.for_day(launch).id == "binary-partition"
    dates = (launch + timedelta(days=i) for i in range(366))
    assert {game.for_day(day).id for day in dates} == {entry.id for entry in bank}
    for lang in ("he", "en"):
        assert len({entry.title[lang] for entry in bank}) == len(bank)
        assert len({entry.prompt[lang] for entry in bank}) == len(bank)


def test_secondary_screenshots_have_transcribed_archival_sources(interview_catalog):
    archive = SEEDS.parents[1] / "interview_preparation"
    transcripts = {
        (q, path)
        for manifest in (archive / "intakes").glob("*sources.json")
        for item in json.loads(manifest.read_text(encoding="utf-8"))["sources"]
        if item.get("original_prompt", "").strip()
        for q in item.get("question_ids", [])
        for path in item.get("archive_paths", [])[:1]
    }
    batches = json.loads((SEEDS / "daily_puzzles.json").read_text(encoding="utf-8"))
    historical = json.dumps(batches[:2], sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert hashlib.sha256(historical.encode()).hexdigest() == "5c1a32eaa869fd639a76452cd423ef292f720598d8f1b34882eef2ff5ec10a64"
    fresh = batches[2]["puzzles"]
    assert len(fresh) == len({item["duplicate_source"] for item in fresh}) == 100
    assert len({item["source_question_key"] for item in fresh}) == 100
    for item in fresh:
        resource = interview_catalog.questions[item["source_question_key"]].assets["preparation_resource"]
        path = item["duplicate_source"]
        assert (archive / path).is_file()
        record = next(s for s in resource["sources"][1:] if s.get("path") == path)
        assert record.get("original_prompt", "").strip() or (resource["id"], path) in transcripts


def test_rotation_keeps_old_days_and_uses_each_puzzle_once_per_deck(interview_catalog):
    entries = load_daily_bank(interview_catalog, SEEDS)
    activation = date(2026, 11, 19)
    game = DailyPuzzleService(lambda: entries)
    old = DailyPuzzleService(lambda: tuple(entry for entry in entries if entry.available_from < activation))
    for offset in range(1, 5):
        day = activation - timedelta(days=offset)
        assert game.for_day(day).id == old.for_day(day).id
    assert game.for_day(activation).available_from == activation
    schedule = [game.for_day(activation + timedelta(days=i)) for i in range(400)]
    expected = {entry.id for entry in entries}
    assert {entry.id for entry in schedule[:200]} == expected
    assert {entry.id for entry in schedule[200:]} == expected
    yesterday = old.for_day(activation - timedelta(days=1))
    assert all(a.source_question_key != b.source_question_key for a, b in pairwise([yesterday, *schedule]))


def test_primary_screenshot_cannot_be_claimed_as_a_duplicate(interview_catalog, tmp_path):
    batch = json.loads((SEEDS / "daily_puzzles.json").read_text(encoding="utf-8"))[-1]
    item = batch["puzzles"][0]
    question = interview_catalog.questions[item["source_question_key"]]
    item["duplicate_source"] = question.assets["preparation_resource"]["sources"][0]["path"]
    batch["puzzles"] = [item]
    (tmp_path / "daily_puzzles.json").write_text(json.dumps([batch]), encoding="utf-8")
    with pytest.raises(ValueError, match="missing secondary question screenshot"):
        load_daily_bank(interview_catalog, tmp_path)


@pytest.mark.parametrize("error", ["missing_variant", "missing_translation", "primary_prompt", "duplicate_variant"])
def test_stale_or_unplayable_variant_fails_without_a_main_prompt_fallback(interview_catalog, tmp_path, error):
    batches = json.loads((SEEDS / "daily_puzzles.json").read_text(encoding="utf-8"))
    item = next(entry for entry in batches[0]["puzzles"] if entry["id"] == "binary-partition")
    batches[0]["puzzles"] = [item]
    if error == "missing_variant":
        item["variant_key_he"] = "removed localized variant"
    elif error == "missing_translation":
        item["en"]["solution"] = ""
    elif error == "primary_prompt":
        item["he"]["prompt"] = interview_catalog.questions[item["source_question_key"]].text("he").prompt
    else:
        batches[0]["puzzles"].append({**item, "id": "a-second-name-for-the-same-puzzle"})
    (tmp_path / "daily_puzzles.json").write_text(json.dumps(batches), encoding="utf-8")
    with pytest.raises(ValueError, match="missing he variant|incomplete en text|main question|duplicate puzzle"):
        load_daily_bank(interview_catalog, tmp_path)
