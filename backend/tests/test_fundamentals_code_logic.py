"""Check the authored short solutions against independent examples and small models.

The executed Python is trusted, repository-authored teaching content, not learner input.
"""

from __future__ import annotations

import ast
import itertools
import json
from collections import Counter, deque
from pathlib import Path

import pytest

CONTENT = Path(__file__).resolve().parents[2] / "apps/web/src/content/fundamentals-code-logic.json"
CARDS = json.loads(CONTENT.read_text(encoding="utf-8"))
BY_ID = {card["id"]: card for card in CARDS}


def authored_function(number: int):
    """Load the one complete function actually displayed on an authored card."""
    source = BY_ID[f"quick-sw-{number:02d}"]["code"]["text"]
    tree = ast.parse(source)
    assert len(tree.body) == 1 and isinstance(tree.body[0], ast.FunctionDef)
    namespace = {}
    exec(compile(tree, str(CONTENT), "exec"), namespace)  # noqa: S102
    return namespace[tree.body[0].name]


def small_lists(values=(-2, 0, 1), max_length=4):
    for length in range(max_length + 1):
        for items in itertools.product(values, repeat=length):
            yield list(items)


def test_bilingual_card_contract_and_five_line_limit():
    assert len(CARDS) == len(BY_ID) == 30
    assert [card["id"] for card in CARDS] == [f"quick-sw-{i:02d}" for i in range(1, 31)]
    assert Counter(card["topic"] for card in CARDS) == {
        "python": 10, "algorithms": 10, "reasoning": 10,
    }
    snippets = []
    for card in CARDS:
        assert set(card) <= {"id", "topic", "title", "prompt", "answer", "takeaway", "code"}
        for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
            assert set(card[field]) == {"he", "en"}
            for language in ("he", "en"):
                text = card[field][language]
                assert isinstance(text, str) and text.strip()
                assert len(text.split()) <= limit, (card["id"], field, language)
        if "code" in card:
            code = card["code"]
            assert code["language"] == "python"
            assert 1 <= len(code["text"].splitlines()) <= 5
            snippets.append(card["id"])
    assert len(snippets) >= 12
    assert snippets == [f"quick-sw-{i:02d}" for i in (*range(1, 12), 14, 15, 16, 18, 19)]


def test_presence_and_occurrence_count():
    contains = authored_function(1)
    occurrences = authored_function(2)
    for values in small_lists():
        original = values[:]
        for target in (-3, -2, 0, 1, 4):
            expected = sum(value == target for value in values)
            assert contains(values, target) is (expected > 0)
            assert occurrences(values, target) == expected
        assert values == original


@pytest.mark.parametrize(
    ("values", "expected"),
    [([], None), ([1, 3, -5], None), ([3, 0, 2], 0), ([-3, -4, 2], -4), ([8, 2], 8)],
)
def test_first_even_preserves_original_order(values, expected):
    original = values[:]
    assert authored_function(3)(values) == expected
    assert values == original


def test_deduplication_keeps_first_occurrences_and_input():
    function = authored_function(4)
    for values in small_lists(max_length=5):
        original = values[:]
        expected = list(dict.fromkeys(values))
        result = function(values)
        assert result == expected
        assert result is not values
        assert values == original


@pytest.mark.parametrize("values", [[], [1], [-2, 0, -2, 4]])
def test_copy_is_independent_of_original(values):
    original = values[:]
    copy = authored_function(5)(values)
    assert copy == values and copy is not values
    copy.append(99)
    assert values == original


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [(6, 3, 2.0), (1, 2, 0.5), (-9, 3, -3.0), (0, 7, 0.0), (9, 0, None), (0, 0, None)],
)
def test_division_handles_zero_before_dividing(a, b, expected):
    assert authored_function(6)(a, b) == expected


def test_squares_handle_negatives_zero_and_empty_input():
    function = authored_function(7)
    for values in small_lists():
        original = values[:]
        assert function(values) == list(map(lambda value: value**2, values))
        assert values == original


@pytest.mark.parametrize(
    ("score", "expected"),
    [(-100, False), (-1, False), (0, True), (1, True), (99, True), (100, True), (101, False)],
)
def test_score_includes_both_boundaries(score, expected):
    assert authored_function(8)(score) is expected


@pytest.mark.parametrize("text", ["", "a", "aba", "A a!", "שלום שלום", "\n \n", "🙂a🙂"])
def test_character_count_includes_spaces_and_distinguishes_case(text):
    assert authored_function(9)(text) == dict(Counter(text))


@pytest.mark.parametrize(
    ("words", "expected"),
    [([], ""), (["a"], "a"), (["a", "b", "c"], "a,b,c"), (["", ""], ","), (["שלום", "עולם"], "שלום,עולם")],
)
def test_join_does_not_add_an_extra_separator(words, expected):
    original = words[:]
    assert authored_function(10)(words) == expected
    assert words == original


def test_maximum_matches_independent_builtin_even_when_all_negative():
    function = authored_function(11)
    for values in small_lists(values=(-9, -3, -1, 0, 5)):
        original = values[:]
        assert function(values) == max(values, default=None)
        assert values == original


def test_flags_find_every_possible_missing_position_in_either_input_order():
    function = authored_function(14)
    for n in range(1, 15):
        for missing in range(1, n + 1):
            values = [value for value in range(1, n + 1) if value != missing]
            for ordered in (values, list(reversed(values))):
                original = ordered[:]
                assert function(ordered, n) == [missing]
                assert ordered == original


def test_pair_search_requires_distinct_indices_and_allows_equal_values():
    function = authored_function(15)
    assert function([3], 6) is False
    assert function([3, 3], 6) is True
    for values in small_lists(max_length=5):
        possible_sums = {a + b for a, b in itertools.combinations(values, 2)}
        original = values[:]
        for target in range(-5, 5):
            assert function(values, target) is (target in possible_sums)
        assert values == original


def test_palindromes_match_symmetric_index_pairs():
    function = authored_function(16)
    for values in small_lists(max_length=5):
        expected = all(values[i] == values[len(values) - 1 - i] for i in range(len(values) // 2))
        original = values[:]
        assert function(values) is expected
        assert values == original


def test_sorted_check_matches_independent_sorting_oracle():
    function = authored_function(18)
    for values in small_lists(max_length=5):
        original = values[:]
        assert function(values) is (values == sorted(values))
        assert values == original


def test_rotation_matches_index_mapping_and_leaves_input_unchanged():
    function = authored_function(19)
    for values in small_lists(max_length=5):
        original = values[:]
        expected = [values[(index + 1) % len(values)] for index in range(len(values))]
        result = function(values)
        assert result == expected
        assert result is not values
        assert values == original


def test_two_coin_flip_puzzle_has_exactly_even_head_counts():
    """Explore all reachable states instead of assuming the claimed invariant."""
    reached = {0}
    queue = deque([0])
    flips = [(1 << a) | (1 << b) for a, b in itertools.combinations(range(10), 2)]
    while queue:
        state = queue.popleft()
        for flip in flips:
            next_state = state ^ flip
            if next_state not in reached:
                reached.add(next_state)
                queue.append(next_state)
    assert {state.bit_count() for state in reached} == {0, 2, 4, 6, 8, 10}
    assert len(reached) == 512


def test_three_color_socks_guarantee_needs_four_draws():
    assert any(len(set(draws)) == 3 for draws in itertools.product(range(3), repeat=3))
    assert all(len(set(draws)) < 4 for draws in itertools.product(range(3), repeat=4))


def test_wrong_label_box_draw_uniquely_determines_all_contents():
    """0=apple, 1=orange, 2=mixed; indices are the printed labels."""
    possibilities = [
        contents for contents in itertools.permutations(range(3))
        if all(label != actual for label, actual in enumerate(contents))
    ]
    assert len(possibilities) == 2
    for drawn_fruit in (0, 1):
        compatible = [contents for contents in possibilities if contents[2] == drawn_fruit]
        assert len(compatible) == 1
        other_fruit = 1 - drawn_fruit
        assert compatible[0][other_fruit] == 2
        assert compatible[0][drawn_fruit] == other_fruit


def test_one_weighing_distinguishes_each_known_heavy_coin():
    outcomes = {}
    for heavy in range(3):
        weights = [2 if coin == heavy else 1 for coin in range(3)]
        outcome = (weights[0] > weights[1]) - (weights[0] < weights[1])
        assert outcome not in outcomes
        outcomes[outcome] = heavy
    assert outcomes == {1: 0, -1: 1, 0: 2}


def test_blue_shirt_rule_has_a_nonprogrammer_counterexample():
    candidates = [(programmer, blue) for programmer, blue in itertools.product((False, True), repeat=2)]
    obeys_rule = [(programmer, blue) for programmer, blue in candidates if not programmer or blue]
    assert (False, True) in obeys_rule
