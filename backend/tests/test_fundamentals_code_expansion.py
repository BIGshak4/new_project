"""Check the twelve new short software cards against independent small oracles."""

from __future__ import annotations

import itertools
import json
from collections import Counter
from functools import cache
from pathlib import Path

import pytest

CONTENT = Path(__file__).resolve().parents[2] / "apps" / "web" / "src" / "content"
CARDS = json.loads((CONTENT / "fundamentals-code-expansion.json").read_text(encoding="utf-8"))
BY_ID = {card["id"]: card for card in CARDS}


def authored_function(number):
    namespace = {}
    exec(BY_ID[f"quick-sw-{number}"]["code"]["text"], namespace)
    functions = [value for key, value in namespace.items() if key != "__builtins__"]
    assert len(functions) == 1 and callable(functions[0])
    return functions[0]


def short_lists(alphabet=(-2, 0, 3), max_length=5):
    for length in range(max_length + 1):
        for values in itertools.product(alphabet, repeat=length):
            yield list(values)


def test_twelve_new_bilingual_cards_keep_reserved_ids_and_short_contract():
    assert len(CARDS) == len(BY_ID) == 12
    assert [card["id"] for card in CARDS] == [f"quick-sw-{number}" for number in range(89, 101)]
    assert Counter(card["topic"] for card in CARDS) == {"algorithms": 8, "python": 4}
    existing = []
    for filename in ("fundamentals-hardware.json", "fundamentals-code-logic.json"):
        existing.extend(json.loads((CONTENT / filename).read_text(encoding="utf-8")))
    assert not set(BY_ID).intersection(card["id"] for card in existing)
    for field in ("title", "prompt"):
        for language in ("he", "en"):
            new_texts = [card[field][language] for card in CARDS]
            assert len(set(new_texts)) == 12
            assert not set(new_texts).intersection(card[field][language] for card in existing)
    for card in CARDS:
        assert set(card) <= {"id", "topic", "title", "prompt", "answer", "takeaway", "code"}
        assert {"id", "topic", "title", "prompt", "answer", "takeaway"} <= set(card)
        for field, word_limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
            assert set(card[field]) == {"he", "en"}
            for language in ("he", "en"):
                text = card[field][language]
                assert isinstance(text, str) and text.strip()
                assert len(text.split()) <= word_limit, (card["id"], field, language)
                assert "\ufffd" not in text
                if language == "he":
                    assert any("\u0590" <= character <= "\u05ff" for character in text)
        if "code" in card:
            assert card["code"]["language"] == "python"
            assert 1 <= len(card["code"]["text"].splitlines()) <= 5


def test_stock_profit_matches_all_legal_buy_sell_pairs_without_reordering():
    profit = authored_function(89)
    for prices in short_lists(alphabet=(0, 1, 4, 9)):
        original = prices[:]
        possibilities = [prices[sell] - prices[buy] for buy, sell in itertools.combinations(range(len(prices)), 2)]
        assert profit(prices) == max([0, *possibilities])
        assert prices == original
    huge = 10 ** 1000
    assert profit([huge, 1, huge + 7]) == huge + 6
    assert profit([9, 7, 1]) == 0
    assert profit([5]) == 0


def test_kadane_restart_rule_matches_all_nonempty_suffixes_not_an_empty_zero():
    answer = BY_ID["quick-sw-90"]["answer"]["en"]
    assert "Restart: 4 exceeds -3+4=1" in answer
    assert "all-negative" in answer and "nonempty" in BY_ID["quick-sw-90"]["prompt"]["en"]
    for values in short_lists(max_length=5):
        for end in range(1, len(values)):
            previous_suffix_best = max(sum(values[start:end]) for start in range(end))
            direct_best = max(sum(values[start:end + 1]) for start in range(end + 1))
            assert direct_best == max(values[end], previous_suffix_best + values[end])
    assert max(sum([-5, -2, -8][start:end]) for start in range(3) for end in range(start + 1, 4)) == -2


def test_stable_sort_preserves_every_equal_key_group_and_input():
    order = authored_function(91)
    for keys in short_lists(alphabet=(-1, 0, 1), max_length=5):
        # Reverse names deliberately: sorting ties by name would now be wrong.
        records = [(chr(90 - index), key) for index, key in enumerate(keys)]
        original = records[:]
        expected = [record for key in sorted(set(keys)) for record in records if record[1] == key]
        result = order(records)
        assert result == expected
        assert records == original and result is not records
    assert order([("A", 2), ("B", 1), ("C", 2)]) == [("B", 1), ("A", 2), ("C", 2)]


def test_fisher_yates_self_choice_is_needed_to_reach_every_permutation():
    outcomes = Counter()
    for final_choice, middle_choice in itertools.product(range(3), range(2)):
        items = list("ABC")
        items[2], items[final_choice] = items[final_choice], items[2]
        items[1], items[middle_choice] = items[middle_choice], items[1]
        outcomes[tuple(items)] += 1
    assert set(outcomes) == set(itertools.permutations("ABC"))
    assert set(outcomes.values()) == {1}
    forced_departure = set()
    for final_choice, middle_choice in itertools.product(range(2), range(2)):
        items = list("ABC")
        items[2], items[final_choice] = items[final_choice], items[2]
        items[1], items[middle_choice] = items[middle_choice], items[1]
        forced_departure.add(tuple(items))
    assert all(items[-1] != "C" for items in forced_departure)
    assert "including a self-swap" in BY_ID["quick-sw-92"]["answer"]["en"]


def test_linked_list_intersection_uses_identity_even_when_values_match():
    common = {"value": 5, "next": None}
    first = {"value": 7, "next": common}
    second = {"value": 7, "next": common}
    assert first == second and first is not second
    paths = ([first, common], [second, common])
    actual = [left for left in paths[0] if any(left is right for right in paths[1])]
    assert len(actual) == 1 and actual[0] is common
    assert BY_ID["quick-sw-93"]["answer"]["en"].startswith("C is the first shared node.")


def test_timestamp_resolution_matches_an_eager_array_for_short_write_histories():
    # Each operation is a global write or a write to one of two cells.
    operations = [(target, value) for target in (None, 0, 1) for value in (-1, 4)]
    for history in itertools.product(operations, repeat=3):
        eager = [0, 0]
        for target, value in history:
            if target is None:
                eager = [value, value]
            else:
                eager[target] = value
        for cell in (0, 1):
            local = [(time, value) for time, (target, value) in enumerate(history, 1) if target == cell]
            global_ = [(time, value) for time, (target, value) in enumerate(history, 1) if target is None]
            latest_local = max([(0, 0), *local])
            latest_global = max([(0, 0), *global_])
            assert max(latest_local, latest_global)[1] == eager[cell]
    answer = BY_ID["quick-sw-94"]["answer"]["en"]
    assert answer.startswith("First 9, then 4") and "do not overflow" in answer


def test_memoization_computes_three_new_values_but_makes_extra_cache_requests():
    computed, requested = [], []

    def request(number):
        requested.append(number)
        return fibonacci(number)

    @cache
    def fibonacci(number):
        if number < 2:
            return number
        computed.append(number)
        return request(number - 1) + request(number - 2)

    fibonacci(0)
    fibonacci(1)
    assert request(4) == 3
    assert Counter(computed) == {2: 1, 3: 1, 4: 1}
    assert requested.count(2) == 2 and len(requested) > len(computed)
    assert "three new subproblems" in BY_ID["quick-sw-95"]["answer"]["en"]


def test_window_updates_match_independently_summed_slices_at_every_legal_width():
    windows = authored_function(96)
    for values in short_lists():
        original = values[:]
        for width in range(1, len(values) + 1):
            expected = [sum(values[start:start + width]) for start in range(len(values) - width + 1)]
            assert windows(values, width) == expected
        assert values == original
    assert windows([2, 5, 1], 2) == [7, 6]


def test_zero_and_none_are_distinct_search_outcomes():
    def detect(result):
        return result is not None

    assert detect(0) and not bool(0)
    assert detect(1) and not detect(None)
    assert "result is not None" in BY_ID["quick-sw-97"]["answer"]["en"]


@pytest.mark.parametrize("number", range(-20, 21))
def test_independent_conditions_preserve_both_labels(number):
    expected = list(filter(None, ["positive" if number in range(1, 21) else "", "even" if number in range(-20, 21, 2) else ""]))
    assert authored_function(98)(number) == expected


def test_default_list_is_fresh_but_an_explicit_list_is_used_even_when_empty():
    append = authored_function(99)
    first, second = append("A"), append("B")
    assert first == ["A"] and second == ["B"] and first is not second
    supplied = []
    assert append("C", supplied) is supplied
    assert supplied == ["C"]
    assert append("D", supplied) is supplied
    assert supplied == ["C", "D"]
    assert append("E", None) == ["E"]


def test_inclusive_sum_matches_pairing_formula_and_zero_boundary():
    total = authored_function(100)
    for number in range(101):
        assert total(number) == number * (number + 1) // 2
    assert total(0) == 0 and total(1) == 1
