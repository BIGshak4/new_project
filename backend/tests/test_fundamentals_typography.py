"""Learner-copy checks that leave code and deliberate mathematical notation intact."""
from __future__ import annotations

import itertools
import importlib.util
import json
import re
from pathlib import Path

import pytest

CONTENT = Path(__file__).resolve().parents[2] / "apps/web/src/content"
CARDS = [
    card
    for path in sorted(CONTENT.glob("fundamentals-*.json"))
    if path.name != "fundamentals-revisions.json"
    for card in json.loads(path.read_bytes())
]


@pytest.mark.parametrize("card", CARDS, ids=lambda card: card["id"])
def test_localized_prose_has_readable_punctuation_and_no_direction_overrides(card):
    for field, language in itertools.product(
        ("title", "prompt", "answer", "takeaway"), ("he", "en")
    ):
        text = card[field][language]
        context = (card["id"], field, language)
        assert text.count("`") % 2 == 0, context
        assert not re.search(r"[\ufffd\u202a-\u202e\u2066-\u2069]", text), context
        if language == "en":
            assert not re.search(r"[\u0590-\u05ff]", text), context
        prose = re.sub(r"`[^`]*`", "", text)
        # Numeric ratios (MUX 2:1), times, ranges and function calls are valid.
        assert not re.search(r";\S|:[A-Za-z\u05d0-\u05ea]", prose), context


def test_mismatched_brackets_remain_literal_example_not_prose_parentheses():
    card = next(card for card in CARDS if card["id"] == "quick-sw-124")
    for language in ("he", "en"):
        assert "`([)]`" in card["prompt"][language]
        assert "`)`" in card["answer"][language]
        assert "`[`" in card["answer"][language]
    # The example is intentionally invalid even though its counts match.
    value = "([)]"
    assert value.count("(") == value.count(")")
    assert value.count("[") == value.count("]")
    assert value[1] != { ")": "(", "]": "[" }[value[2]]


def test_secded_zero_parity_error_flag_is_not_an_assertion_of_bad_parity():
    card = next(card for card in CARDS if card["id"] == "quick-hw-161")
    assert "דגל שגיאת הזוגיות" in card["prompt"]["he"]
    assert "parity-error flag" in card["prompt"]["en"]
    for language in ("he", "en"):
        assert "S=0" in card["prompt"][language]
        assert "P=0" in card["prompt"][language]
    assert card["answer"]["en"].startswith("No error under the promise.")
    # Independently enumerate the stated <=2-fault model: the zero syndrome
    # and zero error flag identify the no-fault case, including the parity bit.
    matching_faults = []
    for count in range(3):
        for positions in itertools.combinations(range(1, 14), count):
            syndrome = 0
            for bit in positions:
                if bit != 13:
                    syndrome ^= bit
            if syndrome == 0 and count % 2 == 0:
                matching_faults.append(positions)
    assert matching_faults == [()]


def test_singular_wording_does_not_rewrite_binary_value_notation():
    path = CONTENT.parents[3] / "backend/scripts/quiz_authoring/hardware_400.py"
    spec = importlib.util.spec_from_file_location("copy_hardware400", path)
    author = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(author)
    text = author.clean("0/1 bits; 1 bits; 11 bits; 1 clock edges")
    assert text == "0/1 bits; 1 bit; 11 bits; 1 clock edge"
