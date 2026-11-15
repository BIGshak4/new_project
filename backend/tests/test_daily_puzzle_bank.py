import json
from datetime import date, timedelta
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
    assert len(bank) >= 100
    assert len({p.source_question_key for p in bank}) >= 60
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
