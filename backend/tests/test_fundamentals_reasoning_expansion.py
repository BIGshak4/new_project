"""Independent finite models for the 28 authored reasoning micro-exercises.

The cards contain proofs in prose rather than executable solutions. These checks
enumerate the underlying worlds, schedules, states and outcomes, including the
counterexamples needed by the proposed answers.
"""

from __future__ import annotations

import itertools
import json
import math
from collections import deque
from fractions import Fraction
from functools import cache
from pathlib import Path

import pytest

CONTENT_DIR = Path(__file__).resolve().parents[2] / "apps/web/src/content"
CARDS = json.loads(
    (CONTENT_DIR / "fundamentals-reasoning-expansion.json").read_text(encoding="utf-8")
)
BY_ID = {card["id"]: card for card in CARDS}


def assert_numeric_claim(number: int, text: str) -> None:
    """Bind the independently computed numerical result to both displayed answers."""
    for language in ("he", "en"):
        assert text in BY_ID[f"quick-sw-{number}"]["answer"][language]


def test_expansion_contract_and_no_exact_reuse_of_existing_cards():
    assert len(CARDS) == len(BY_ID) == 28
    assert list(BY_ID) == [f"quick-sw-{number}" for number in range(61, 89)]
    old_cards = []
    for source in ("fundamentals-hardware.json", "fundamentals-code-logic.json"):
        old_cards.extend(json.loads((CONTENT_DIR / source).read_text(encoding="utf-8")))
    assert set(BY_ID).isdisjoint(card["id"] for card in old_cards)
    for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
        for language in ("he", "en"):
            values = [card[field][language] for card in CARDS]
            old_values = {card[field][language] for card in old_cards}
            assert len(set(values)) == len(values)
            assert set(values).isdisjoint(old_values)
            for card, value in zip(CARDS, values, strict=True):
                assert value.strip() and len(value.split()) <= limit, (card["id"], field, language)
                assert "\ufffd" not in value
                if language == "he":
                    assert any("\u0590" <= char <= "\u05ff" for char in value)
    for card in CARDS:
        assert card["topic"] == "reasoning"
        assert set(card) == {"id", "topic", "title", "prompt", "answer", "takeaway"}
        for field in ("title", "prompt", "answer", "takeaway"):
            assert set(card[field]) == {"he", "en"}


def test_61_midpoint_requires_each_coordinate_not_just_total_parity():
    points = list(itertools.product(range(-3, 4), repeat=2))
    for left, right in itertools.product(points, repeat=2):
        midpoint = tuple(Fraction(a + b, 2) for a, b in zip(left, right, strict=True))
        integral = all(value.denominator == 1 for value in midpoint)
        assert integral == all(a % 2 == b % 2 for a, b in zip(left, right, strict=True))
    assert tuple(Fraction(a + b, 2) for a, b in zip((2, 5), (8, 1), strict=True)) == (5, 3)
    assert sum((1, 2)) + sum((2, 1)) == 6
    assert Fraction(1 + 2, 2).denominator != 1
    assert_numeric_claim(61, "(5,3)")


def test_62_pooled_test_signatures_decode_every_contaminated_bottle():
    pools = ({"B", "D"}, {"C", "D"})
    signatures = {bottle: tuple(bottle in pool for pool in pools) for bottle in "ABCD"}
    assert len(set(signatures.values())) == 4
    assert signatures == {
        "A": (False, False), "B": (True, False),
        "C": (False, True), "D": (True, True),
    }
    for poisoned in "ABCD":
        observed = tuple(bool(pool & {poisoned}) for pool in pools)
        assert [bottle for bottle, signature in signatures.items() if signature == observed] == [poisoned]


def test_63_identical_movement_preserves_the_initial_separation():
    for commands in itertools.product((-1, 0, 1), repeat=6):
        positions = [0, 7]
        for delta in commands:
            positions = [position + delta for position in positions]
            assert positions[1] - positions[0] == 7
            assert positions[0] != positions[1]


@pytest.mark.parametrize("proposed_bound", (1, 2, 5, 10, 100, 1000))
def test_64_arbitrarily_long_unfair_prefix_can_precede_a_fair_cycle(proposed_bound):
    prefix = ["A"] * proposed_bound
    cycle = ("A", "B", "C")
    assert set(prefix) != set(cycle)
    # Repeating this finite cycle forever visits every participant infinitely often.
    assert set(cycle) == {"A", "B", "C"}
    assert set(prefix + list(cycle)) == set(cycle)


def test_65_blind_coin_partition_works_for_every_initial_and_selected_triple():
    triples = list(itertools.combinations(range(12), 3))
    for heads in triples:
        original_heads = set(heads)
        for chosen in triples:
            selected = set(chosen)
            flipped_selected_heads = selected - original_heads
            unchanged_other_heads = original_heads - selected
            assert len(flipped_selected_heads) == len(unchanged_other_heads)


def test_66_repeated_signals_do_not_count_distinct_senders_but_one_use_does():
    assert len(("A", "A", "A")) == 3
    assert len(set(("A", "A", "A"))) == 1
    for visits in itertools.product("ABC", repeat=6):
        sent = set()
        signals = []
        for visitor in visits:
            if visitor not in sent:
                sent.add(visitor)
                signals.append(visitor)
        assert len(signals) == len(set(visits))
        if len(signals) == 3:
            assert set(signals) == {"A", "B", "C"}


def test_67_allowed_adjacent_pairs_cannot_extend_past_the_dead_end():
    allowed = {"12", "23"}

    def valid(digits):
        return digits.startswith("1") and all(digits[i:i + 2] in allowed for i in range(len(digits) - 1))

    length_three = ["".join(chars) for chars in itertools.product("123", repeat=3)]
    length_four = ["".join(chars) for chars in itertools.product("123", repeat=4)]
    assert [digits for digits in length_three if valid(digits)] == ["123"]
    assert not any(valid(digits) for digits in length_four)


def test_68_every_move_from_eight_has_a_winning_opponent_response():
    @cache
    def wins(total):
        return any(total + move == 12 or not wins(total + move)
                   for move in (1, 2, 3) if total + move <= 12)

    assert not wins(8)
    assert all(wins(8 + move) for move in (1, 2, 3))
    for move in (1, 2, 3):
        reply = 4 - move
        assert reply in (1, 2, 3)
        assert 8 + move + reply == 12


def test_69_joint_crossing_cost_is_bottleneck_plus_sequential_return():
    crossing_times = (2, 7)
    completion = next(t for t in range(1, 10) if all(t >= duration for duration in crossing_times))
    assert completion == 7
    total = completion + crossing_times[0]
    assert total == 9
    assert_numeric_claim(69, str(total))


def test_70_shortest_job_first_minimizes_sum_of_completion_times():
    def completion_sum(order):
        time = total = 0
        for duration in order:
            time += duration
            total += time
        return total

    assert {order: completion_sum(order) for order in itertools.permutations((1, 4))} == {
        (1, 4): 6, (4, 1): 9,
    }
    for short in range(1, 6):
        for long in range(short, 8):
            assert completion_sum((short, long)) <= completion_sum((long, short))
    assert_numeric_claim(70, "6")
    assert_numeric_claim(70, "9")


def test_71_complement_probability_matches_full_outcome_enumeration():
    outcomes = list(itertools.product("HT", repeat=3))
    favorable = [outcome for outcome in outcomes if "H" in outcome]
    probability = Fraction(len(favorable), len(outcomes))
    assert probability == 1 - Fraction(1, 8) == Fraction(7, 8)
    assert_numeric_claim(71, str(probability))


@pytest.mark.parametrize("p", [Fraction(i, 10) for i in range(1, 10)])
def test_72_rejection_extractor_is_fair_for_different_biases(p):
    probabilities = {
        "HH": p * p, "HT": p * (1 - p),
        "TH": (1 - p) * p, "TT": (1 - p) * (1 - p),
    }
    accepted = probabilities["HT"] + probabilities["TH"]
    assert accepted > 0
    assert probabilities["HT"] / accepted == probabilities["TH"] / accepted == Fraction(1, 2)
    rejected = probabilities["HH"] + probabilities["TT"]
    assert 0 < rejected < 1
    # Any finite number of rejections is possible, despite geometric convergence.
    assert rejected**20 > 0


def test_73_public_ignorance_eliminates_every_world_with_a_black_front_hat():
    # World tuple: (front, rear), with B=black and W=white.
    worlds = [(front, rear) for front, rear in itertools.product("WB", repeat=2)
              if (front, rear) != ("B", "B")]
    remaining = []
    for front, rear in worlds:
        own_colors_possible = {other_rear for other_front, other_rear in worlds if other_front == front}
        if len(own_colors_possible) > 1:
            remaining.append((front, rear))
    assert set(remaining) == {("W", "W"), ("W", "B")}
    assert {front for front, _ in remaining} == {"W"}


def test_74_repeating_xor_observation_cannot_separate_zero_zero_and_one_one():
    worlds = list(itertools.product((0, 1), repeat=2))
    compatible = [world for world in worlds if world[0] ^ world[1] == 0]
    assert compatible == [(0, 0), (1, 1)]
    repeated = {world: (world[0] ^ world[1],) * 10 for world in compatible}
    assert len(set(repeated.values())) == 1
    assert len({world[0] for world in compatible}) == 2


def test_75_every_reachable_marble_distribution_has_odd_total_and_unequal_counts():
    seen = {(2, 5)}
    queue = deque(seen)
    while queue:
        left, right = queue.popleft()
        candidates = []
        if left:
            candidates.append((left - 1, right + 1))
        if right:
            candidates.append((left + 1, right - 1))
        for state in candidates:
            if state not in seen:
                seen.add(state)
                queue.append(state)
    assert len(seen) == 8
    assert all(left + right == 7 and left != right for left, right in seen)


def test_76_exact_real_halving_decreases_without_finite_zero():
    value = Fraction(1)
    for step in range(1, 1001):
        previous = value
        value /= 2
        assert value == Fraction(1, 2**step)
        assert 0 < value < previous
    # Positivity follows for every finite step: a positive numerator over 2**k.
    # Integer division is deliberately a different process and does terminate.
    integer_value = 128
    integer_steps = 0
    while integer_value:
        integer_value //= 2
        integer_steps += 1
    assert integer_steps == 8
    assert_numeric_claim(76, "1/2^k")


def test_77_language_group_overlap_matches_inclusion_exclusion():
    people = set(range(10))
    python = set(range(6))
    possibilities = [set(group) for group in itertools.combinations(people, 5)]
    compatible_c_groups = [group for group in possibilities if python | group == people]
    assert compatible_c_groups
    assert {len(python & group) for group in compatible_c_groups} == {1}
    for group in possibilities:
        assert len(python | group) == len(python) + len(group) - len(python & group)


def test_78_exhaustive_minimax_with_one_ball_requires_four_drops():
    infinity = float("inf")

    @cache
    def minimum_drops(thresholds, balls):
        if len(thresholds) <= 1:
            return 0
        if balls == 0:
            return infinity
        best = infinity
        for floor in range(1, 5):
            broken = tuple(threshold for threshold in thresholds if threshold <= floor)
            intact = tuple(threshold for threshold in thresholds if threshold > floor)
            if not broken or not intact:
                continue  # A result known in advance supplies no information.
            cost = 1 + max(minimum_drops(broken, balls - 1), minimum_drops(intact, balls))
            best = min(best, cost)
        return best

    # Threshold 5 represents no break on any of the four available floors.
    assert minimum_drops((1, 2, 3, 4, 5), 1) == 4
    for threshold in range(1, 6):
        observations = tuple(floor >= threshold for floor in range(1, 5))
        # Stop at the first break; all-intact observations identify threshold 5.
        first_break = next((floor for floor in range(1, 5) if observations[floor - 1]), 5)
        assert first_break == threshold
    assert_numeric_claim(78, "4")


def test_79_decimal_digit_sum_preserves_remainder_modulo_three():
    for number in range(10000):
        digit_sum = sum(int(digit) for digit in str(number))
        assert number % 3 == digit_sum % 3
    assert 123 % 3 == (1 + 2 + 3) % 3 == 0


def test_80_inverses_must_be_applied_in_reverse_order():
    for initial in range(-20, 21):
        result = 2 * initial + 3
        assert Fraction(result - 3, 2) == initial
    assert Fraction(17 - 3, 2) == 7
    assert Fraction(17, 2) - 3 != 7
    assert_numeric_claim(80, "7")


def test_81_unrolled_helix_has_constant_five_unit_length():
    for segments in range(1, 101):
        length = segments * math.hypot(Fraction(3, segments), Fraction(4, segments))
        assert math.isclose(length, 5, rel_tol=1e-12)
    assert_numeric_claim(81, "5")


def test_82_odd_divisor_count_occurs_exactly_at_perfect_squares_including_one():
    for number in range(1, 401):
        divisors = [divisor for divisor in range(1, number + 1) if number % divisor == 0]
        square = math.isqrt(number) ** 2 == number
        assert (len(divisors) % 2 == 1) == square
        self_pairs = [divisor for divisor in divisors if divisor == number // divisor]
        assert len(self_pairs) == int(square)
        assert {number // divisor for divisor in divisors} == set(divisors)


def test_83_median_is_the_unique_minimizer_of_three_house_distances():
    def total_distance(point):
        return sum(abs(point - house) for house in (0, 4, 10))

    points = [Fraction(quarter, 4) for quarter in range(-8, 49)]
    values = {point: total_distance(point) for point in points}
    assert min(values.values()) == 10
    assert [point for point, total in values.items() if total == 10] == [4]
    assert total_distance(Fraction(14, 3)) > total_distance(4)  # The arithmetic mean loses.
    assert_numeric_claim(83, "10")


def test_84_transitive_race_constraints_exclude_c_from_the_top_two():
    consistent_orders = [order for order in itertools.permutations("ABCDE")
                         if order.index("A") < order.index("B") < order.index("C")]
    assert consistent_orders
    assert min(order.index("C") for order in consistent_orders) == 2
    assert all("C" not in order[:2] for order in consistent_orders)


def test_85_expectation_need_not_be_an_attainable_die_outcome():
    outcomes = tuple(range(1, 7))
    expectation = sum(Fraction(outcome, len(outcomes)) for outcome in outcomes)
    assert expectation == Fraction(7, 2)
    assert expectation not in outcomes
    assert_numeric_claim(85, "3.5")


def test_86_independent_next_toss_is_fair_even_after_four_heads():
    outcomes = list(itertools.product("HT", repeat=5))
    retained = [outcome for outcome in outcomes if outcome[:4] == ("H",) * 4]
    probability = Fraction(sum(outcome[-1] == "T" for outcome in retained), len(retained))
    assert probability == Fraction(1, 2)
    assert_numeric_claim(86, str(probability))


def test_87_largest_coin_greedy_loses_to_independent_minimum_coin_oracle():
    remaining = 6
    greedy = []
    while remaining:
        chosen = max(coin for coin in (1, 3, 4) if coin <= remaining)
        greedy.append(chosen)
        remaining -= chosen
    assert greedy == [4, 1, 1]
    minimum = next(count for count in range(1, 7)
                   if any(sum(coins) == 6 for coins in itertools.product((1, 3, 4), repeat=count)))
    assert minimum == 2 < len(greedy)
    assert 6 not in (1, 3, 4)
    assert_numeric_claim(87, "3+3")


def test_88_cyclic_winners_admit_no_consistent_total_ranking():
    beats = {("R", "G"), ("G", "B"), ("B", "R")}
    rankings = [order for order in itertools.permutations("RGB")
                if all((order[i], order[j]) in beats for i in range(3) for j in range(i + 1, 3))]
    assert rankings == []
    assert all(any((other, first) in beats for other in "RGB") for first in "RGB")
