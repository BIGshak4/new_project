"""Replay every authored hardware quiz case independently of answer positions."""

from __future__ import annotations

import importlib.util
import itertools
import json
import re
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
SHARDS = ROOT / "backend/seeds/duel_quiz_batches"
spec = importlib.util.spec_from_file_location(
    "hardware400", ROOT / "backend/scripts/quiz_authoring/hardware_400.py"
)
AUTHOR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AUTHOR)
CARDS = json.loads((CONTENT / "fundamentals-hardware-400.json").read_bytes())
QUIZ = json.loads((SHARDS / "hardware_400.json").read_bytes())
CHECKS = json.loads((SHARDS / "hardware_400.checks.json").read_bytes())
BY_KEY = {q["key"]: q for q in QUIZ}


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c["key"])
def test_actual_case_against_independent_oracle(check):
    # This replay does not infer truth from the correct-choice index.
    AUTHOR.verify(check["method"], check["inputs"], check["expected"])
    row = BY_KEY[check["key"]]
    assert row["choices"][row["correct"]] == check["correct_text"]
    independent_text = AUTHOR.choices(check["method"], check["expected"])[0]
    assert check["correct_text"] == {lang: AUTHOR.clean(text) for lang, text in independent_text.items()}


def test_short_card_schema_sources_lengths_and_all_prior_prompts():
    prep = {
        q["id"] for q in json.loads((ROOT / "interview_preparation/questions.json").read_bytes())["questions"]
    }
    prior = []
    for name in (
        "fundamentals-hardware.json",
        "fundamentals-hardware-expansion.json",
        "fundamentals-hardware-250.json",
        "fundamentals-code-logic.json",
        "fundamentals-code-expansion.json",
        "fundamentals-code-250.json",
        "fundamentals-reasoning-expansion.json",
        "fundamentals-reasoning-250.json",
    ):
        prior.extend(json.loads((CONTENT / name).read_bytes()))
    assert len(prior) == 250
    assert {c["id"] for c in CARDS} == {f"quick-hw-{n}" for n in range(126, 201)}
    assert len(CARDS) == 75
    for card in CARDS:
        assert card["interviewIds"] and set(card["interviewIds"]) <= prep
        assert card["topic"] in {"bits", "gates", "states", "sequential", "electronics"}
        assert "solution_review" not in card and "company" not in card
        for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
            assert set(card[field]) == {"he", "en"}
            for lang, text in card[field].items():
                assert text.strip() == text and len(text.split()) <= limit, (card["id"], field, lang)
                assert "\ufffd" not in text
                if lang == "en":
                    assert not re.search(r"[\u0590-\u05ff]", text)
        if "code" in card:
            assert len(card["code"]["text"].splitlines()) <= 5
    for lang, field in itertools.product(("he", "en"), ("title", "prompt")):
        values = [c[field][lang].casefold().strip() for c in [*prior, *CARDS]]
        assert len(values) == len(set(values))


def test_quiz_has_five_distinct_four_choice_drafts_per_source():
    assert len(QUIZ) == len(BY_KEY) == len(CHECKS) == 375
    grouped = {card["id"]: [] for card in CARDS}
    for row in QUIZ:
        assert row["status"] == "draft"
        assert row["key"] == f"{row['source_key']}-v{row['variant']}"
        assert len(row["choices"]) == 4
        assert type(row["correct"]) is int and 0 <= row["correct"] < 4
        grouped[row["source_key"]].append(row)
        for lang in ("he", "en"):
            assert len({c[lang].strip().casefold() for c in row["choices"]}) == 4
            for text in [row["prompt"][lang], row["explanation"][lang], *(c[lang] for c in row["choices"])]:
                assert text and text == text.strip() and "\ufffd" not in text
                if lang == "en":
                    assert not re.search(r"[\u0590-\u05ff]", text)
    for rows in grouped.values():
        assert sorted(q["variant"] for q in rows) == [1, 2, 3, 4, 5]
        for lang in ("he", "en"):
            assert len({q["prompt"][lang] for q in rows}) == 5
    assert (
        max(Counter(q["correct"] for q in QUIZ).values()) - min(Counter(q["correct"] for q in QUIZ).values())
        <= 1
    )


def test_generator_reproduces_actual_published_source_artifacts_without_writing():
    rows, checks = AUTHOR.build()
    assert rows == QUIZ
    assert checks == CHECKS
    assert AUTHOR.CARDS == CARDS


def test_error_and_prefix_examples_follow_full_input_history():
    run = AUTHOR.source_model("prep_171_completed_run_parity")
    prefix = AUTHOR.source_model("prep_173_overlapping_1011")
    assert run.detect([0, 0]) == [0, 0]
    assert run.detect([0, 0, 1]) == [0, 0, 1]
    assert prefix.detections([1, 0, 1, 1, 0, 1, 1]) == [0, 0, 0, 1, 0, 0, 1]
    for a, b, cin in itertools.product((0, 1), repeat=3):
        c1, c2 = a & b, (a ^ b) & cin
        assert not (c1 and c2)
        assert (c1 | c2) == (c1 ^ c2) == ((a + b + cin) // 2)


def test_analog_examples_do_not_claim_general_timing_guarantees():
    assert AUTHOR.model("buffer_delay", dict(rs=10, cin=1, rb=1, cl=1, tb=10)) > 10
    assert AUTHOR.model("overshoot", dict(before=3, jump=3)) > 3
    assert AUTHOR.model("lc_half", dict(v0=3)) < 0
    assert AUTHOR.model("alias", dict(frequency=18, fs=20)) == 2
