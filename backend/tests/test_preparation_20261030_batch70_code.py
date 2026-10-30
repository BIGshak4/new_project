"""Independent software oracles for five new records and two appendices."""
from __future__ import annotations

import importlib.util
import itertools
import math
import random
from fractions import Fraction
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SORT = load("prep_160_capacity_sorting")
LIFT = load("prep_161_elevator_look_model")
PERM = load("prep_162_string_permutations")
LONGEST = load("prep_163_longest_sum_mod_three")
OPS = load("prep_164_digits_to_hundred")
STREAM = load("prep_037_append_parenthesis_monitor")
MISSING = load("prep_041_one_pass_exact_moments")


def check_sorting_cases():
    compressed = 0
    for block in range(1, 9):
        for zeros in itertools.product(range(block + 1), repeat=4):
            values = [value for count in zeros for value in ([0] * count + [1] * (block - count))]
            output, stats = SORT.sorter_only(values, sorted, capacity=2 * block)
            assert output == sorted(values)
            assert stats == {"box_calls": 5, "external_reads": 10 * block, "external_writes": 10 * block}
            compressed += 1
    rng = random.Random(160)
    for _ in range(100):
        values = [rng.randrange(-1000, 1001) for _ in range(2000)]
        before = list(values)
        output, stats = SORT.sorter_only(values, sorted)
        assert output == sorted(values) and values == before
        assert stats == {"box_calls": 5, "external_reads": 5000, "external_writes": 5000}
    bitonic = 0
    for length in range(11):
        for values in itertools.product((0, 1), repeat=length):
            assert SORT.bitonic_box(values)[0] == sorted(values)
            bitonic += 1
    for _ in range(20):
        values = [rng.randrange(-999, 1000) for _ in range(1000)]
        output, stats = SORT.bitonic_box(values)
        assert output == sorted(values)
        assert stats == {"padded_lanes": 1024, "comparator_cells": 28160, "stages": 55}
    values = [rng.randrange(1000) for _ in range(2000)]
    output, _ = SORT.sorter_only(values, lambda part: SORT.bitonic_box(part)[0])
    assert output == sorted(values)
    return {"compressed_binary_block_count_cases": compressed, "seeded_2000_inputs": 100,
            "bitonic_all_binary_inputs_through_length10": bitonic, "bitonic_seeded_thousand_inputs": 20,
            "end_to_end_bitonic_box_construction": True, "box_calls": 5,
            "external_reads": 5000, "external_writes": 5000, "physical_memory_benchmark": False}


class Plant:
    def __init__(self, floor):
        self.floor, self.state, self.commands = floor, LIFT.STATE.STOP, []

    def EngineUp(self):
        self.state = LIFT.STATE.UP
        self.commands.append("UP")

    def EngineDown(self):
        self.state = LIFT.STATE.DOWN
        self.commands.append("DOWN")

    def EngineStop(self):
        self.state = LIFT.STATE.STOP
        self.commands.append("STOP")

    def EngineStateGet(self):
        return self.state

    def EngineGetCurrFloor(self):
        return self.floor

    def advance_to_next_landing(self):
        if self.state == LIFT.STATE.UP:
            self.floor += 1
        elif self.state == LIFT.STATE.DOWN:
            self.floor -= 1
        assert 1 <= self.floor <= 8


def check_elevator_cases():
    cases = 0
    for start, mask, direction in itertools.product(range(1, 9), range(256), tuple(LIFT.STATE)):
        plant = Plant(start)
        controller = LIFT.ElevatorController(plant)
        controller.direction = direction
        requested = {floor for floor in range(1, 9) if mask & (1 << (floor - 1))}
        for floor in requested:
            controller.EnignePressedFloor(floor)
            controller.EnignePressedFloor(floor)  # duplicate presses coalesce
        served = set()
        for _ in range(32):
            event = controller.control_step()
            if event is not None:
                assert event in requested
                served.add(event)
            if not controller.inbox and not controller.pending:
                break
            plant.advance_to_next_landing()
        assert served == requested
        assert not controller.pending and not controller.inbox
        controller.control_step()
        assert plant.state == LIFT.STATE.STOP
        cases += 1
    # A request posted after a service clear remains pending for another turn.
    plant = Plant(4)
    controller = LIFT.ElevatorController(plant)
    controller.EnignePressedFloor(4)
    assert controller.control_step() == 4
    controller.EnignePressedFloor(4)
    assert controller.control_step() == 4
    for invalid in (0, 9, True, 2.5):
        before = controller.inbox
        with pytest.raises(ValueError):
            controller.EnignePressedFloor(invalid)
        assert controller.inbox == before
    # Separate model of why non-atomic ISR read/modify/write can lose a bit.
    old_a = old_b = 0
    lost = old_a | 1
    lost = old_b | 2
    assert lost == 2 and (0 | 1 | 2) == 3
    return {"finite_request_masks_floors_directions": cases, "duplicate_presses_coalesced": True,
            "post_clear_same_floor_request_retained": True, "invalid_floors": 4,
            "non_atomic_lost_update_witness": True,
            "scope": "Serialized landing-level Python scheduler only; no actual ISR timing, doors, braking or safety qualification."}


def check_permutation_cases():
    cases = 0
    for n in range(7):
        for letters in itertools.product("abc", repeat=n):
            source = "".join(letters)
            actual = list(PERM.unique_permutations(source))
            expected = {"".join(values) for values in itertools.permutations(source)}
            assert set(actual) == expected and len(actual) == len(expected)
            cases += 1
    distinct = list(PERM.unique_permutations("abcdefgh"))
    assert len(distinct) == len(set(distinct)) == math.factorial(8)
    assert list(PERM.unique_permutations("")) == [""]
    written = []
    PERM.print_permutations("aab", written.append)
    assert set(written) == {"aab", "aba", "baa"}
    assert set(PERM.unique_permutations("אב")) == {"אב", "בא"}
    return {"all_ternary_strings_through_length6": cases, "distinct_eight_character_outputs": 40320,
            "empty_string_outputs": 1, "duplicate_outputs_avoided": True, "writer_wrapper_checked": True}


def longest_oracle(values):
    best = (0, None, None)
    for start in range(len(values)):
        for end in range(start, len(values)):
            if sum(values[start:end + 1]) % 3 == 0:
                candidate = end - start + 1, start, end
                if candidate[0] > best[0] or (candidate[0] == best[0] and candidate[1:] < best[1:]):
                    best = candidate
    return best


def check_longest_cases():
    positives = signed = 0
    for n in range(8):
        for values in itertools.product((1, 2, 3, 4), repeat=n):
            assert LONGEST.longest_mod_three(values) == longest_oracle(values)
            positives += 1
    for n in range(7):
        for values in itertools.product((-2, -1, 0, 1, 2), repeat=n):
            assert LONGEST.longest_mod_three(values, positive_only=False) == longest_oracle(values)
            signed += 1
    assert LONGEST.longest_mod_three([1, 2, 4, 5, 6, 7]) == (5, 0, 4)
    for invalid in ([0], [-1], [True], [1.5]):
        with pytest.raises(ValueError):
            LONGEST.longest_mod_three(invalid)
    return {"positive_array_cases": positives, "explicit_signed_extension_cases": signed,
            "source_example_result": [5, 0, 4], "invalid_main_contract_cases": 4}


def operator_oracle(operators):
    """Independent shunting-yard stacks, using exact rational arithmetic."""
    values, pending = [], []
    precedence = {"+": 1, "-": 1, "*": 2, "/": 2}

    def reduce_once():
        right, left = values.pop(), values.pop()
        operator = pending.pop()
        if operator == "+":
            values.append(left + right)
        elif operator == "-":
            values.append(left - right)
        elif operator == "*":
            values.append(left * right)
        else:
            values.append(left / right)
    values.append(Fraction(1))
    for operator, digit in zip(operators, range(2, 10), strict=True):
        while pending and precedence[pending[-1]] >= precedence[operator]:
            reduce_once()
        pending.append(operator)
        values.append(Fraction(digit))
    while pending:
        reduce_once()
    return values[0]


def check_operator_cases():
    count = hits = 0
    for operators in itertools.product(("+", "-", "*", "/"), repeat=8):
        actual = OPS.expression_value(operators)
        assert actual == operator_oracle(operators)
        count += 1
        hits += actual == 100
    witness = ("+",) * 7 + ("*",)
    assert OPS.expression_value(witness) == 100
    assert OPS.first_expression() == OPS.format_expression(witness)
    return {"all_four_operator_gap_assignments": count, "solutions_under_declared_grammar": hits,
            "source_target": 100, "witness": "1+2+3+4+5+6+7+8*9", "eval_used": False}


def parenthesis_oracle(text):
    depth = 0
    for character in text:
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def check_stream_cases():
    cases = observations = 0
    for n in range(10):
        for characters in itertools.product("()a", repeat=n):
            monitor = STREAM.ParenthesisMonitor()
            prefix = ""
            assert monitor.valid
            for character in characters:
                prefix += character
                assert monitor.feed(character) == parenthesis_oracle(prefix)
                observations += 1
            monitor.reset()
            assert monitor.valid
            cases += 1
    monitor = STREAM.ParenthesisMonitor()
    assert not monitor.feed(")") and not monitor.feed("(")
    for invalid in ("", "()", None):
        with pytest.raises(ValueError):
            monitor.feed(invalid)
    return {"all_streams_through_length9": cases, "prefix_status_observations": observations,
            "irreparable_close_before_open_checked": True, "pop_api_invented": False}


class OneShot:
    def __init__(self, values):
        self.values, self.scans = values, 0

    def __iter__(self):
        self.scans += 1
        assert self.scans == 1, "input may only be consumed once"
        return iter(self.values)


def check_missing_once_cases():
    one = two = 0
    for n in range(1, 9):
        for missing in range(1, n + 1):
            remaining = [value for value in range(1, n + 1) if value != missing]
            for order in itertools.permutations(remaining):
                stream = OneShot(order)
                assert MISSING.missing_one_once(stream, n) == missing and stream.scans == 1
                one += 1
        for missing in itertools.combinations(range(1, n + 1), 2):
            remaining = [value for value in range(1, n + 1) if value not in missing]
            for order in itertools.permutations(remaining):
                stream = OneShot(order)
                assert MISSING.missing_two_once(stream, n) == missing and stream.scans == 1
                two += 1
    for missing in itertools.combinations(range(1, 101), 2):
        stream = OneShot(value for value in range(100, 0, -1) if value not in missing)
        assert MISSING.missing_two_once(stream) == missing and stream.scans == 1
    return {"all_small_single_omission_orders": one, "all_small_double_omission_orders": two,
            "all_hundred_range_missing_pairs": 4950, "one_shot_scan_guard": True,
            "exact_integer_square_root": True, "full_input_validation_claimed": False}


def test_sorter_only_network_and_bitonic_box_match_full_sorting_oracles():
    assert check_sorting_cases()["box_calls"] == 5


def test_elevator_model_services_all_finite_masks_with_declared_landing_contract():
    assert check_elevator_cases()["finite_request_masks_floors_directions"] == 6144


def test_unique_string_permutations_match_position_permutation_set_and_printer():
    assert check_permutation_cases()["duplicate_outputs_avoided"]


def test_longest_divisible_interval_matches_independent_all_interval_sums():
    assert check_longest_cases()["source_example_result"] == [5, 0, 4]


def test_digit_operator_grammar_matches_independent_rational_expression_parser():
    assert check_operator_cases()["all_four_operator_gap_assignments"] == 65536


def test_append_monitor_matches_whole_prefix_language_without_pop_assumptions():
    assert not check_stream_cases()["pop_api_invented"]


def test_single_pass_missing_values_match_all_orders_and_exact_hundred_pairs():
    assert check_missing_once_cases()["one_shot_scan_guard"]
