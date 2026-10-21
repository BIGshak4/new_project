"""Check the authored short solutions against independent examples and small models.

The executed Python is trusted, repository-authored teaching content, not learner input.
"""

from __future__ import annotations

import ast
import itertools
import json
from collections import Counter, deque
from fractions import Fraction
from pathlib import Path

import pytest

CONTENT = Path(__file__).resolve().parents[2] / "apps/web/src/content/fundamentals-code-logic.json"
CARDS = json.loads(CONTENT.read_text(encoding="utf-8"))
BY_ID = {card["id"]: card for card in CARDS}


def answer(number: int) -> str:
    return BY_ID[f"quick-sw-{number:02d}"]["answer"]["en"]


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
    assert len(CARDS) == len(BY_ID) == 60
    assert [card["id"] for card in CARDS] == [f"quick-sw-{i:02d}" for i in range(1, 61)]
    assert Counter(card["topic"] for card in CARDS) == {
        "python": 6, "algorithms": 12, "reasoning": 42,
    }
    assert len({card["prompt"]["he"] for card in CARDS}) == 60
    assert len({card["prompt"]["en"] for card in CARDS}) == 60
    snippets = []
    for card in CARDS:
        assert set(card) <= {"id", "topic", "title", "prompt", "answer", "takeaway", "code"}
        for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
            assert set(card[field]) == {"he", "en"}
            for language in ("he", "en"):
                text = card[field][language]
                assert isinstance(text, str) and text.strip()
                assert len(text.split()) <= limit, (card["id"], field, language)
                assert "\ufffd" not in text
                if language == "he":
                    assert any("\u0590" <= char <= "\u05ff" for char in text)
        if "code" in card:
            code = card["code"]
            assert code["language"] == "python"
            assert 1 <= len(code["text"].splitlines()) <= 5
            snippets.append(card["id"])
    assert snippets == [f"quick-sw-{i:02d}" for i in (3, 5, 9, 11, 14, 15, 18, 31, 32, 33)]


@pytest.mark.parametrize(
    ("values", "expected"),
    [([], None), ([1, 3, -5], None), ([3, 0, 2], 0), ([-3, -4, 2], -4), ([8, 2], 8)],
)
def test_first_even_preserves_original_order(values, expected):
    original = values[:]
    assert authored_function(3)(values) == expected
    assert values == original


@pytest.mark.parametrize("values", [[], [1], [-2, 0, -2, 4]])
def test_copy_is_independent_of_original(values):
    original = values[:]
    copy = authored_function(5)(values)
    assert copy == values and copy is not values
    copy.append(99)
    assert values == original


@pytest.mark.parametrize("text", ["", "a", "aba", "A a!", "שלום שלום", "\n \n", "🙂a🙂"])
def test_character_count_includes_spaces_and_distinguishes_case(text):
    assert authored_function(9)(text) == dict(Counter(text))


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


def test_sorted_check_matches_independent_sorting_oracle():
    function = authored_function(18)
    for values in small_lists(max_length=5):
        original = values[:]
        assert function(values) is (values == sorted(values))
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


def test_new_python_functions_match_independent_oracles_without_mutating_input():
    positive_sum = authored_function(31)
    reverse_text = authored_function(32)
    swapped = authored_function(33)
    for values in small_lists(values=(-8, -1, 0, 2, 7)):
        original = values[:]
        assert positive_sum(values) == sum(filter(lambda number: number > 0, values))
        assert values == original
    for length in range(6):
        for letters in itertools.product("aBZ", repeat=length):
            text = "".join(letters)
            expected = "".join(text[index] for index in range(len(text) - 1, -1, -1))
            assert reverse_text(text) == expected
    for first, second in itertools.product(range(-3, 4), repeat=2):
        assert swapped(first, second) == (second, first)


def test_one_true_box_statement_has_only_one_compatible_location():
    statements = {
        location: (location != "A", location == "A", location != "B")
        for location in "ABC"
    }
    assert [location for location, truths in statements.items() if sum(truths) == 1] == ["B"]
    assert answer(1).startswith("In B.")


def test_parallel_machine_schedule_includes_indivisible_last_part():
    completion_times = [max(first, 5 - first) * 4 for first in range(6)]
    assert min(completion_times) == 12
    assert all(2 * (minute // 4) < 5 for minute in range(12))
    assert answer(2).startswith("12 minutes")


def test_line_constraints_have_exactly_one_order():
    orders = [
        order for order in itertools.permutations("ABCD")
        if order[0] == "D" and order.index("A") < order.index("B") < order.index("C")
    ]
    assert orders == [("D", "A", "B", "C")]
    assert "D, A, B, C" in answer(4)


def test_average_speed_uses_total_distance_and_total_time():
    durations = [Fraction(60, speed) for speed in (30, 60)]
    assert 120 / sum(durations) == 40
    assert sum((30, 60)) / 2 != 40
    assert answer(6).startswith("40 km/h")


def test_flashing_lights_first_positive_shared_event():
    matches = sorted(set(range(6, 61, 6)) & set(range(10, 61, 10)))
    assert matches[0] == 30
    assert answer(7).startswith("After 30 seconds")


def test_stair_sequences_are_ordered_and_exhaustive():
    routes = {
        route for length in range(1, 4)
        for route in itertools.product((1, 2), repeat=length) if sum(route) == 3
    }
    assert routes == {(1, 1, 1), (1, 2), (2, 1)}
    assert answer(8).startswith("Three sequences")


def test_age_difference_is_unchanged_by_equal_increments():
    assert (13 + 5) - (8 + 5) == 5
    assert answer(10).startswith("5 years")


def test_conditional_coin_probability_enumerates_retained_trials():
    retained = [outcome for outcome in itertools.product(("H", "T"), repeat=2) if "H" in outcome]
    assert len(retained) == 3
    assert Fraction(sum(outcome == ("H", "H") for outcome in retained), len(retained)) == Fraction(1, 3)
    assert answer(13).startswith("1/3")


def test_pursuit_meets_at_correct_time_and_position():
    catch_time = Fraction(4, 3 - 1)
    assert catch_time == 2
    assert 3 * catch_time == 4 + 1 * catch_time == 6
    assert answer(16).startswith("After 2 seconds")


def test_missing_corners_leave_unequal_colors_and_no_domino_tiling():
    cells = frozenset(itertools.product(range(4), repeat=2)) - {(0, 0), (3, 3)}
    assert Counter((row + column) % 2 for row, column in cells) == {0: 6, 1: 8}

    def can_tile(remaining):
        if not remaining:
            return True
        row, column = min(remaining)
        for neighbor in ((row + 1, column), (row - 1, column), (row, column + 1), (row, column - 1)):
            if neighbor in remaining and can_tile(remaining - {(row, column), neighbor}):
                return True
        return False

    assert not can_tile(cells)
    assert answer(19).startswith("No.")
    assert "6 squares" in answer(19) and "8 of the other" in answer(19)


def test_two_balanced_binary_questions_distinguish_four_boxes():
    outcomes = {(key in "AB", key in "AC") for key in "ABCD"}
    assert len(outcomes) == 4
    assert len({False, True}) < 4
    assert answer(20).startswith("2 questions")


def test_binary_search_and_merge_examples_discard_only_impossible_choices():
    values, target = [2, 5, 9, 12, 16, 20, 25], 20
    middle = len(values) // 2
    assert values[middle] == 12
    assert target not in values[:middle + 1]
    assert target in values[middle + 1:]
    assert "right half: [16, 20, 25]" in answer(12)
    assert sorted([1, 7] + [3, 4])[0] == 1
    assert answer(17).startswith("Take 1 from the first list")


def test_remaining_original_short_puzzles_have_concrete_models():
    assert 7 - 4 == 3
    assert "4-minute glass empties" in answer(23) and "7-minute glass empties" in answer(23)
    runners = ["leader", "second", "you"]
    runners[1], runners[2] = runners[2], runners[1]
    assert runners.index("you") + 1 == 2
    assert answer(24).startswith("Second place.")
    large, small, capacity = 5, 0, 3
    transferred = min(large, capacity - small)
    assert (large - transferred, small + transferred) == (2, 3)
    assert "Exactly 2 liters remain" in answer(27)
    players, games = list(range(8)), 0
    while len(players) > 1:
        players = players[::2]
        games += len(players)
    assert games == 7
    assert answer(28).startswith("Seven games.")
    assert len(list(itertools.combinations("ABCD", 2))) == 6
    assert answer(29).startswith("Six:")


def test_stack_and_queue_examples_distinguish_removal_order():
    stack = ["A", "B"]
    assert stack.pop() == "B"
    stack.append("C")
    assert stack.pop() == "C"
    queue = deque(["A", "B"])
    assert queue.popleft() == "A"
    queue.append("C")
    assert queue.popleft() == "B"
    assert answer(34).startswith("C.")
    assert answer(35).startswith("B.")


def test_repeated_set_insertions_do_not_add_occurrences():
    values = set()
    for value in (4, 2, 4):
        values.add(value)
    assert values == {2, 4} and len(values) == 2
    assert answer(36).startswith("Two elements: 2 and 4.")


def test_linked_list_order_follows_links_not_names():
    following = {"A": "C", "C": "B", "B": None}
    visited, current = [], "A"
    while current is not None:
        visited.append(current)
        current = following[current]
    assert visited == ["A", "C", "B"]
    assert answer(37).startswith("A, C, B")


def test_linear_search_worst_case_visits_all_ten_items():
    values = [4, 8, 1, 6, 9, 2, 7, 3, 0, 5]
    for target in (-1, 5):
        comparisons = 0
        for value in values:
            comparisons += 1
            if value == target:
                break
        assert comparisons == 10
    assert answer(38).startswith("10 comparisons")


def test_prefix_difference_matches_every_subrange_not_only_the_example():
    values = [2, 3, 1, 4]
    prefixes = [sum(values[:end]) for end in range(len(values) + 1)]
    assert prefixes == [0, 2, 5, 6, 10]
    for start in range(len(values)):
        for end in range(start, len(values)):
            assert prefixes[end + 1] - prefixes[start] == sum(values[start:end + 1])
    assert prefixes[3] - prefixes[1] == 4
    assert answer(39).startswith("The sum is 4:")


def test_grid_routes_and_outfits_count_distinct_choices():
    routes = set(itertools.permutations("RRU"))
    assert routes == {("R", "R", "U"), ("R", "U", "R"), ("U", "R", "R")}
    assert len(list(itertools.product(range(2), range(3)))) == 6
    assert answer(40).startswith("3 routes")
    assert answer(41).startswith("6 outfits")


def test_photograph_relation_identifies_the_speaker_as_father():
    father = {"speaker": "grandfather", "pictured_boy": "speaker"}
    only_son_of = {"grandfather": "speaker"}
    assert father["pictured_boy"] == only_son_of[father["speaker"]] == "speaker"
    assert answer(42).startswith("The speaker is the boy’s father.")


def test_other_guard_question_always_points_at_trap():
    for exit_door, asked_guard_truthful in itertools.product((0, 1), (False, True)):
        other_guard_truthful = not asked_guard_truthful
        other_guard_reply = exit_door if other_guard_truthful else 1 - exit_door
        reported_reply = other_guard_reply if asked_guard_truthful else 1 - other_guard_reply
        assert reported_reply == 1 - exit_door
        assert 1 - reported_reply == exit_door
    assert "Choose the opposite door" in answer(43)


def test_marble_sum_and_difference_have_one_nonnegative_solution():
    candidates = [(a, b) for a, b in itertools.product(range(11), repeat=2) if a + b == 10 and a - b == 2]
    assert candidates == [(6, 4)]
    assert answer(44).startswith("The first has 6 and the second 4.")


def test_chocolate_complete_break_sequences_always_need_five_moves():
    """Enumerate legal rectangle splits instead of assuming a piece-count formula."""
    states = {((2, 3),)}
    for breaks in range(6):
        finished = [state for state in states if all(piece == (1, 1) for piece in state)]
        if finished:
            assert breaks == 5
            break
        next_states = set()
        for state in states:
            for index, (rows, columns) in enumerate(state):
                other_pieces = list(state[:index] + state[index + 1:])
                splits = [((cut, columns), (rows - cut, columns)) for cut in range(1, rows)]
                splits += [((rows, cut), (rows, columns - cut)) for cut in range(1, columns)]
                for pieces in splits:
                    next_states.add(tuple(sorted(other_pieces + list(pieces))))
        states = next_states
    else:
        pytest.fail("No complete chocolate split was reached")
    assert answer(45).startswith("5 breaks")


def test_box_upper_bound_rules_out_thirty_one_for_all_contents():
    totals = {sum(contents) for contents in itertools.product((2, 3), repeat=10)}
    assert min(totals) == 20 and max(totals) == 30 and 31 not in totals
    assert "at most 30" in answer(46)


def test_shared_time_window_matches_hour_by_hour_availability():
    first_free, second_free = set(range(9, 12)), set(range(11, 14))
    assert first_free & second_free == {11}
    assert answer(47).startswith("From 11:00 to 12:00: one hour.")


def test_ten_day_trace_ends_on_thursday():
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day = 0
    for _ in range(10):
        day = (day + 1) % len(weekdays)
    assert weekdays[day] == "Thursday"
    assert answer(48).startswith("Thursday.")


def test_divisibility_counterexample_and_square_area_factor():
    assert str(22).endswith("2") and 22 % 4 == 2
    assert answer(49).startswith("No: 22")
    assert Fraction(4 * 4, 2 * 2) == 4
    assert answer(50).startswith("By a factor of 4.")


def test_family_roles_overlap_for_three_distinct_people():
    parent_pairs = {("grandfather", "father"), ("father", "son")}
    fathers = {parent for parent, _ in parent_pairs}
    sons = {child for _, child in parent_pairs}
    assert len(fathers) == len(sons) == 2
    assert len(fathers | sons) == 3
    assert "grandfather, his son, and his grandson" in answer(51)


def test_five_binary_hat_colors_always_include_three_of_one_color():
    for hats in itertools.product(("red", "blue"), repeat=5):
        assert max(Counter(hats).values()) >= 3
    assert answer(52).startswith("Yes.")


def test_identify_third_key_by_eliminating_first_two():
    for correct in range(3):
        candidates = set(range(3))
        trials = 0
        for key in (0, 1):
            trials += 1
            if key == correct:
                candidates = {key}
                break
            candidates.remove(key)
        assert candidates == {correct} and trials <= 2
    assert answer(53).startswith("2 trials")


def test_add_three_or_five_excludes_seven_but_includes_eight():
    reached = {0}
    for value in range(9):
        if value in reached:
            reached.update(value + increment for increment in (3, 5) if value + increment <= 8)
    assert reached == {0, 3, 5, 6, 8}
    assert "7 is impossible" in answer(54) and "Reach 8 using 3+5" in answer(54)


@pytest.mark.parametrize("left_half_minutes", [5, 10, 20, 40, 50, 55])
def test_two_ended_rope_burn_handles_unequal_density_halves(left_half_minutes):
    """Integrate two nonuniform physical halves; the meeting is not halfway along."""
    right_half_minutes = 60 - left_half_minutes
    if left_half_minutes < 30:
        left_front = Fraction(1, 2) + Fraction(30 - left_half_minutes, 2 * right_half_minutes)
        right_front = 1 - Fraction(30, 2 * right_half_minutes)
    else:
        left_front = Fraction(30, 2 * left_half_minutes)
        right_front = Fraction(1, 2) - Fraction(30 - right_half_minutes, 2 * left_half_minutes)
    assert left_front == right_front
    assert left_front != Fraction(1, 2)
    assert "30 minutes" in answer(55)


def test_fair_die_probability_counts_equally_likely_outcomes():
    outcomes = list(range(1, 7))
    assert Fraction(sum(value % 2 == 0 for value in outcomes), len(outcomes)) == Fraction(1, 2)
    assert answer(56).startswith("1/2.")


def test_weights_on_opposite_pans_measure_two_kilograms():
    assert [weight for weight in range(7) if 1 + weight == 3] == [2]
    assert "3−1=2 kg" in answer(57)


def test_two_ternary_weighing_results_have_nine_sequences():
    assert len(set(itertools.product(("left", "balanced", "right"), repeat=2))) == 9
    assert answer(58).startswith("9 sequences.")
    assert "does not guarantee every coin puzzle" in answer(58)


def test_two_is_a_prime_even_counterexample():
    assert [divisor for divisor in range(1, 3) if 2 % divisor == 0] == [1, 2]
    assert 2 % 2 == 0
    assert answer(59).startswith("2 is both prime and even.")


def test_unspecified_bag_counts_allow_different_red_probabilities():
    possible_probabilities = {Fraction(red, red + blue) for red, blue in ((1, 1), (1, 3))}
    assert possible_probabilities == {Fraction(1, 2), Fraction(1, 4)}
    assert answer(60).startswith("No.")
    assert "1/2" in answer(60) and "1/4" in answer(60)
