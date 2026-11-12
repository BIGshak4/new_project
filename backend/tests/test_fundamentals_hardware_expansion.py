"""Independent checks for the 40 hardware fundamentals added to the 200-card set.

Truth tables, integer arithmetic, observable traces and a deque serve as oracles.
These are logical content checks, not HDL compilation or physical timing analysis.
"""

from __future__ import annotations

import itertools
import json
import math
import re
from collections import Counter, deque
from fractions import Fraction
from pathlib import Path

import pytest

CONTENT = Path(__file__).resolve().parents[2] / "apps/web/src/content"
CARDS = json.loads((CONTENT / "fundamentals-hardware-expansion.json").read_text(encoding="utf-8"))
BY_ID = {question["id"]: question for question in CARDS}


def card(number):
    return BY_ID[f"quick-hw-{number}"]


def backticks(number, language="en"):
    return re.findall(r"`([^`]+)`", card(number)["answer"][language])


def assert_in_both(number, text):
    for language in ("he", "en"):
        assert text in card(number)["answer"][language]


def bool_formula(expression, variables):
    """Evaluate the authored Boolean grammar with NOT > AND > XOR > OR."""
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_]*|[01]|[()]", expression)
    assert "".join(tokens) == re.sub(r"\s+", "", expression)
    position = 0

    def atom():
        nonlocal position
        token = tokens[position]
        position += 1
        if token == "NOT":
            return 1 - atom()
        if token == "(":
            value = disjunction()
            assert tokens[position] == ")"
            position += 1
            return value
        if token in variables:
            return variables[token]
        assert token in {"0", "1"}
        return int(token)

    def level(child, operator):
        nonlocal position
        value = child()
        while position < len(tokens) and tokens[position] == operator:
            position += 1
            right = child()
            if operator == "AND":
                value &= right
            elif operator == "XOR":
                value ^= right
            else:
                value |= right
        return value

    def conjunction():
        return level(atom, "AND")

    def exclusive_or():
        return level(conjunction, "XOR")

    def disjunction():
        return level(exclusive_or, "OR")

    result = disjunction()
    assert position == len(tokens)
    return result


def fsm_step(number, state, values):
    possible = []
    for transition in card(number)["diagram"]["transitions"]:
        if transition["from"] != state:
            continue
        label = transition["label"]
        output = None
        if re.fullmatch(r"[01]/[01]", label):
            match, output = map(int, label.split("/"))
            enabled = values["x"] == match
        elif label.startswith("any "):
            assert label[4:] in values
            enabled = True
        else:
            signal, match = label.split("=")
            enabled = values[signal] == int(match)
        if enabled:
            possible.append((transition["to"], output))
    assert len(possible) == 1, (number, state, values, possible)
    return possible[0]


def test_exactly_forty_new_stable_ids_and_no_old_card_replacement():
    previous = json.loads((CONTENT / "fundamentals-hardware.json").read_text(encoding="utf-8"))
    assert len(CARDS) == len(BY_ID) == 40
    assert set(BY_ID) == {f"quick-hw-{number}" for number in range(61, 101)}
    assert not set(BY_ID) & {item["id"] for item in previous}
    assert Counter(item["topic"] for item in CARDS) == {
        "gates": 9, "bits": 8, "sequential": 15, "states": 8,
    }
    for language in ("he", "en"):
        assert len({item["prompt"][language] for item in [*previous, *CARDS]}) == 100
        assert len({item["title"][language] for item in [*previous, *CARDS]}) == 100


@pytest.mark.parametrize("question", CARDS, ids=lambda question: question["id"])
def test_phone_sized_bilingual_contract_without_review_attestation(question):
    required = {"id", "topic", "title", "prompt", "answer", "takeaway"}
    assert required <= question.keys()
    assert question.keys() <= required | {"code", "diagram"}
    for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
        assert set(question[field]) == {"he", "en"}
        for text in question[field].values():
            assert text.strip() and len(text.split()) <= limit
    if "code" in question:
        assert question["code"]["language"] == "verilog"
        assert len(question["code"]["text"].splitlines()) <= 5
    if "diagram" in question:
        diagram = question["diagram"]
        if diagram["kind"] == "gate":
            assert diagram["gate"] in {"AND", "OR", "XOR", "NOT", "MUX"}
        else:
            assert diagram["kind"] == "fsm"
            assert 2 <= len(set(diagram["states"])) <= 4
            assert diagram["initial"] in diagram["states"]
            for transition in diagram["transitions"]:
                assert transition["from"] in diagram["states"]
                assert transition["to"] in diagram["states"]


def test_wide_equality_code_and_expanded_formula_match_all_word_pairs():
    code = card(61)["code"]["text"]
    match = re.fullmatch(r"assign eq = ~\(\|\(([A-Z]) \^ ([A-Z])\)\);", code)
    assert match and match.groups() == ("A", "B")
    formula = backticks(61)[0].removeprefix("eq=")
    for a, b in itertools.product(range(16), repeat=2):
        variables = {f"{name}{index}": (value >> index) & 1
                     for name, value in (("A", a), ("B", b)) for index in range(4)}
        authored_code_result = int((a ^ b) == 0)  # Verilog reduction OR, then one-bit NOT.
        expected = int(all(x == y for x, y in zip(f"{a:04b}", f"{b:04b}", strict=True)))
        assert bool_formula(formula, variables) == authored_code_result == expected


def test_half_adder_equations_and_code_reconstruct_the_integer_sum():
    expressions = dict(expression.split("=", 1) for expression in backticks(62))
    code = card(62)["code"]["text"]
    assert code.splitlines() == ["assign S = A ^ B;", "assign C = A & B;"]
    for a, b in itertools.product((0, 1), repeat=2):
        result = {name: bool_formula(expression, {"A": a, "B": b})
                  for name, expression in expressions.items()}
        assert result["S"] + 2 * result["C"] == a + b


def test_encoder_valid_distinguishes_absence_from_bit_zero():
    expression = next(value.removeprefix("valid=") for value in backticks(63) if value.startswith("valid="))
    for word in range(16):
        variables = {f"x{index}": (word >> index) & 1 for index in range(4)}
        assert bool_formula(expression, variables) == int(word != 0)
    assert (0).bit_length() == 0 and (1).bit_length() - 1 == 0
    assert_in_both(63, "00")


def test_hierarchical_priority_encoder_preserves_highest_index_for_every_word():
    for word in range(1, 2**16):
        groups = [(word >> (4 * group)) & 15 for group in range(4)]
        selected = max(index for index, group in enumerate(groups) if group)
        local = groups[selected].bit_length() - 1
        global_index = (selected << 2) | local
        expected = max(index for index in range(16) if word & (1 << index))
        assert global_index == expected
    example = (2 << 2) | 1
    assert_in_both(64, f"`{example:04b}`")
    # ORing local results is not a selection operation.
    assert ((1 | 2) != 1)  # Higher group local 1, lower group local 2.


def test_fault_activation_requires_opposite_value():
    activating = [x for x in (0, 1) if x != 0]
    assert activating == [int(backticks(65)[0].split("=")[1])]


def test_and_fault_test_is_both_excited_and_observable():
    detecting = [(x, b) for x, b in itertools.product((0, 1), repeat=2) if x * b != 0 * b]
    assert detecting == [(1, 1)]
    expected = ", ".join(f"{name}={value}" for name, value in zip(("X", "B"), detecting[0], strict=True))
    assert_in_both(66, f"`{expected}`")
    assert card(66)["diagram"] == {"kind": "gate", "gate": "AND", "inputs": ["X", "B=1"], "output": "Y"}


def test_redundant_nor_branch_sa0_has_no_distinguishing_vector():
    def output(a, b, c, branch):
        return int(a and not (b or branch) and not c)

    sa0_tests, sa1_tests = [], []
    for a, b, c in itertools.product((0, 1), repeat=3):
        healthy = output(a, b, c, c)
        if healthy != output(a, b, c, 0):
            sa0_tests.append((a, b, c))
        if healthy != output(a, b, c, 1):
            sa1_tests.append((a, b, c))
    assert sa0_tests == []
    assert sa1_tests == [(1, 0, 0)]  # Scope matters: not all branch faults are redundant.
    assert "No A,B,C combination" in card(67)["answer"]["en"]


def test_settled_boolean_zero_can_have_a_path_delay_pulse():
    direct_arrival, inverted_arrival = Fraction(1, 10), Fraction(1, 1)
    observed = []
    for when in (Fraction(0), Fraction(1, 2), Fraction(2)):
        direct = int(when >= direct_arrival)
        inverted = int(when < inverted_arrival)
        observed.append(direct & inverted)
    assert observed == [0, 1, 0]
    assert "may occur" in card(68)["answer"]["en"]
    assert "guarantees neither" in card(68)["answer"]["en"]


def test_tristate_does_not_assert_a_logic_zero():
    answer = card(69)["answer"]["en"]
    assert "forces neither 0 nor 1" in answer and "no logic value is guaranteed" in answer
    assert_in_both(69, "`Z`")


def test_signed_overflow_is_not_unsigned_carry_for_all_four_bit_pairs():
    def signed(word):
        return word - 16 if word >= 8 else word

    for a, b in itertools.product(range(16), repeat=2):
        full_sum = signed(a) + signed(b)
        result = (a + b) & 15
        overflow_by_range = not -8 <= full_sum <= 7
        overflow_by_sign = (a >> 3 == b >> 3) and (result >> 3 != a >> 3)
        assert overflow_by_range == overflow_by_sign
    assert (7 + 1) >> 4 == 0 and not -8 <= 7 + 1 <= 7
    assert_in_both(70, f"`{(7 + 1) & 15:04b}`")


def test_widening_after_truncation_cannot_recover_carry():
    sums = [a + b for a, b in itertools.product(range(16), repeat=2)]
    assert max(sums) == 30 and max(sums).bit_length() == 5
    assert (15 + 1) & 15 == 0
    assert 15 + 1 == 16
    assert_in_both(71, "`1111+0001=10000`")
    assert_in_both(71, "`00000`")


def test_adjacent_average_simplification_for_all_allowed_four_bit_inputs():
    for a in range(14):
        b = a + 2
        assert (a + b) % 2 == 0
        assert (a + b) // 2 == a + 1
        assert a <= a + 1 <= b < 16
    assert_in_both(72, "`(a+b)/2=(a+a+2)/2=a+1`")


def test_minimum_signed_value_needs_widening_before_exact_negation():
    same_width = ((~8 & 15) + 1) & 15
    assert same_width == 8
    sign_extended = 8 | 16
    widened_negation = ((~sign_extended & 31) + 1) & 31
    assert widened_negation == 8 and widened_negation < 16
    assert_in_both(73, "`NOT 1000 = 0111`")
    assert_in_both(73, "`0111+1=1000`")


def test_power_of_two_remainder_matches_low_bit_selection():
    for value in range(2**12):
        assert value % 8 == value & 7
    original, tail = backticks(74)[0].split(" → ")
    assert int(original, 2) % 8 == int(tail, 2) == 5
    assert tail == original[-3:]


def test_gray_codes_have_one_bit_changes_and_match_the_authored_examples():
    gray = [value ^ (value >> 1) for value in range(8)]
    assert all((first ^ second).bit_count() == 1 for first, second in zip(gray, gray[1:], strict=False))
    assert gray[3:5] == [int("010", 2), int("110", 2)]
    assert (3 ^ 4).bit_count() == 3
    assert_in_both(75, "`011 XOR 001 = 010`")
    assert_in_both(75, "`100 XOR 010 = 110`")


def test_occupancy_has_one_more_value_than_the_address_space():
    assert math.ceil(math.log2(8)) == 3
    assert math.ceil(math.log2(len(range(9)))) == 4
    pointer = 0
    empty_pointer = pointer
    for _ in range(8):
        pointer = (pointer + 1) % 8
    assert pointer == empty_pointer  # Same pointer, different occupancy.
    assert backticks(76) == backticks(76, "he") == ["3", "4"]


def test_product_width_covers_every_operand_pair_and_is_minimal():
    products = [a * b for a, b in itertools.product(range(16), repeat=2)]
    assert max(products) == 225
    assert all(value < 2**8 for value in products)
    assert any(value >= 2**7 for value in products)
    assert backticks(77) == backticks(77, "he") == ["15×15=225", "8"]


def test_msb_first_remainder_tracks_prefix_values_without_storing_them():
    for size in range(1, 9):
        for bits in itertools.product((0, 1), repeat=size):
            remainder = prefix = 0
            for bit in bits:
                remainder = (2 * remainder + bit) % 3
                prefix = int(f"{prefix:b}{bit}", 2)
                assert remainder == prefix % 3
    r, example = 0, []
    for x in (1, 1, 0):
        r = (2 * r + x) % 3
        example.append(r)
    assert backticks(78) == backticks(78, "he") == ["r_next=(2r+x) modulo 3", ", ".join(map(str, example))]


def test_synchronous_sr_wiring_is_d_for_each_old_state_and_input():
    assert backticks(79) == backticks(79, "he") == ["S=D, R=NOT D"]
    for old_q, data in itertools.product((0, 1), repeat=2):
        s, r = data, 1 - data
        assert (s, r) != (1, 1)
        result = 0 if r else (1 if s else old_q)
        assert result == data
    answer = card(79)["answer"]["en"]
    assert "synchronous controls" in answer and "does not guarantee a DFF" in answer


def test_latch_and_flip_flop_have_different_between_edge_traces():
    latch_q = ff_q = 0
    for data in (1, 0, 1):
        latch_q = data  # Enable is continuously high; no rising edge occurs.
        assert ff_q == 0
    assert latch_q == 1 and ff_q == 0
    assert "latch follows D while EN=1" in card(80)["answer"]["en"]
    assert "flip-flop holds its sample until the next edge" in card(80)["answer"]["en"]


def test_setup_deadline_is_before_the_capture_edge():
    times = [Fraction(number) for number in re.findall(r"(\d+(?:\.\d+)?)ns", card(81)["prompt"]["en"])]
    capture, setup = times
    deadline = capture - setup
    assert_in_both(81, f"`{deadline}ns`")
    assert deadline < 9 and capture > 9


def test_hold_deadline_is_independent_of_an_unchanged_next_period():
    capture, hold, new_arrival = [Fraction(number) for number in re.findall(
        r"(\d+(?:\.\d+)?)ns", card(82)["prompt"]["en"])]
    deadline = capture + hold
    assert new_arrival < deadline
    assert all(new_arrival < capture + hold for _next_period in (2, 5, 10, 100))
    assert_in_both(82, f"`{deadline}ns`")


def test_parallel_timing_uses_maximum_not_sum():
    assert max(3, 5) + 2 == 7 != 3 + 5 + 2
    assert_in_both(83, "`max(3,5)+2=7ns`")


def test_two_stage_pipeline_reaches_one_result_per_edge_after_fill():
    first = second = None
    output = []
    for value in "ABCD":
        first, second = value, first
        output.append(second)
    assert output == [None, "A", "B", "C"]
    assert "one result per cycle" in card(84)["answer"]["en"]
    assert "latency is two cycles" in card(84)["answer"]["en"]


def test_synchronizer_scope_does_not_claim_a_coherent_multi_bit_snapshot():
    # During 01 -> 10, independent bit sampling can produce combinations absent at the source.
    before, after = (0, 1), (1, 0)
    independent_samples = set(itertools.product(*[{a, b} for a, b in zip(before, after, strict=True)]))
    assert {(0, 0), (1, 1)} <= independent_samples - {before, after}
    answer = card(85)["answer"]["en"]
    assert "reduces failure probability rather than guaranteeing zero" in answer
    assert "does not guarantee a coherent word" in answer


def test_short_pulse_can_be_entirely_absent_at_every_destination_sample():
    pulse_start, pulse_end = Fraction(1, 4), Fraction(1, 2)
    assert pulse_end - pulse_start < 1
    assert not any(pulse_start <= edge < pulse_end for edge in (0, 1, 2))
    assert any(edge >= pulse_start for edge in (1, 2))  # Held request is observable, unlike the pulse.
    assert "holding a request until acknowledged" in card(86)["answer"]["en"]


def test_fifo_count_equation_uses_only_accepted_operations():
    for occupancy, write, read in itertools.product(range(9), (0, 1), (0, 1)):
        queue = deque(range(occupancy))
        pop = bool(read and queue)
        push = bool(write and (len(queue) < 8 or pop))
        if pop:
            queue.popleft()
        if push:
            queue.append("new")
        assert occupancy + push - pop == len(queue)
        assert 0 <= len(queue) <= 8
    assert_in_both(87, "`c_next=c+push-pop`")


def test_full_simultaneous_fifo_operations_preserve_output_order():
    queue = deque("ABC")
    output = queue.popleft()
    queue.append("X")
    assert_in_both(88, f"`{output}`")
    assert_in_both(88, f"`{','.join(queue)}`")
    assert len(queue) == 3
    assert "Same-address memory behavior" in card(88)["answer"]["en"]


def test_empty_fifo_without_bypass_rejects_read_from_preedge_empty():
    queue = deque()
    accepted_read = bool(queue)
    queue.append("X")
    assert not accepted_read and list(queue) == ["X"]
    assert_in_both(89, f"`{len(queue)}`")
    assert "current read request does not return it" in card(89)["answer"]["en"]


def test_stalled_ready_valid_transfer_delivers_original_pending_data_once():
    pending = "A"
    accepted = []
    offers = []
    for ready in (0, 0, 1):
        offers.append((1, pending))
        if ready:
            accepted.append(pending)
    assert offers == [(1, "A")] * 3 and accepted == ["A"]
    assert "until a transfer is accepted" in card(90)["answer"]["en"]
    assert_in_both(90, "`valid=1`")
    assert_in_both(90, "`A`")


def test_saturation_and_wraparound_have_different_boundary_behavior():
    saturated = wrapped = 6
    trace = []
    for _ in range(3):
        saturated = min(saturated + 1, 7)
        wrapped = (wrapped + 1) % 8
        trace.append(saturated)
    assert trace == [7, 7, 7] and wrapped == 1
    assert_in_both(91, f"`{', '.join(map(str, trace))}`")


def test_up_down_bit_toggle_formula_matches_every_old_counter_and_command():
    expression = backticks(92)[0].removeprefix("toggle1=")
    for q, inc, dec in itertools.product(range(8), (0, 1), (0, 1)):
        direction = inc - dec
        next_q = (q + direction) % 8
        expected_toggle = ((q >> 1) & 1) ^ ((next_q >> 1) & 1)
        assert bool_formula(expression, {"inc": inc, "dec": dec, "Q0": q & 1}) == expected_toggle


def test_combinational_default_removes_dependence_on_previous_next_value():
    code = card(93)["code"]["text"]
    statements = code.splitlines()
    default = re.fullmatch(r"\s*next = ([A-Za-z]+);", statements[1])
    override = re.fullmatch(r"\s*if \((\w+)\) next = ([A-Z]+);", statements[2])
    assert statements[0] == "always @* begin" and statements[-1] == "end"
    assert default and override
    for state, previous_next, go in itertools.product(range(4), range(4), (0, 1)):
        signals = {"state": state, "DONE": 3, "go": go}
        next_value = signals[default[1]]
        if signals[override[1]]:
            next_value = signals[override[2]]
        assert next_value == (3 if go else state)
        # With no default, the undriven branch instead depends on old next.
        omitted_default = 3 if go else previous_next
        if not go and previous_next != state:
            assert omitted_default != next_value
    assert_in_both(93, "`next=state`")


def test_two_waiting_states_are_indistinguishable_for_all_short_future_inputs():
    for size in range(8):
        for bits in itertools.product((0, 1), repeat=size):
            states = ["W0", "W1"]
            seen_one = False
            for bit in bits:
                seen_one |= bool(bit)
                states = [fsm_step(94, state, {"x": bit})[0] for state in states]
                outputs = [int(state == "DONE") for state in states]
                assert outputs == [int(seen_one)] * 2
    assert "No future input sequence distinguishes" in card(94)["answer"]["en"]


def test_held_start_does_not_retrigger_after_done_without_release():
    state, starts = "READY", 0
    for _ in range(10):
        next_state, _ = fsm_step(95, state, {"s": 1, "d": 1})
        starts += int(state == "READY" and next_state == "RUN")
        state = next_state
    assert state == "WAIT" and starts == 1
    state, _ = fsm_step(95, state, {"s": 0, "d": 0})
    assert state == "READY"
    state, _ = fsm_step(95, state, {"s": 1, "d": 0})
    assert state == "RUN"
    assert "requires sampling s=0 in WAIT" in card(95)["answer"]["en"]


def test_rearm_fsm_defines_one_transition_for_every_state_and_input_pair():
    for state in card(95)["diagram"]["states"]:
        for start, done in itertools.product((0, 1), repeat=2):
            fsm_step(95, state, {"s": start, "d": done})


def test_lsb_first_remainder_needs_weight_phase_and_matches_integer_value():
    for size in range(1, 9):
        for bits in itertools.product((0, 1), repeat=size):
            remainder, weight = 0, 1
            value = 0
            for position, bit in enumerate(bits):
                remainder = (remainder + bit * weight) % 3
                weight = (2 * weight) % 3
                value += bit * (2**position)
                assert remainder == value % 3
                assert weight == (1 if (position + 1) % 2 == 0 else 2)
    wrong_msb_rule = ((2 * 0 + 1) * 2 + 0) % 3
    assert wrong_msb_rule == 2 != int("01", 2) % 3
    assert_in_both(96, "`r_next=(r+x×w) modulo 3`")


def test_quadrature_direction_and_illegal_jump_follow_cycle_order():
    forward = ["00", "01", "11", "10"]
    previous, current = "01", "00"
    assert (forward.index(current) - forward.index(previous)) % 4 == 3
    assert "00" != "11" and sum(a != b for a, b in zip("00", "11", strict=True)) == 2
    assert forward[(0 + 2) % 4] == forward[(0 - 2) % 4] == "11"
    assert_in_both(97, "`01→00`")
    assert_in_both(97, "`00→11`")
    assert "does not establish a unique direction" in card(97)["answer"]["en"]


def test_moore_pulse_has_exactly_two_high_intervals_per_accepted_trigger():
    for bits in itertools.product((0, 1), repeat=8):
        state, remaining = "IDLE", 0
        for trigger in bits:
            state, _ = fsm_step(98, state, {"t": trigger})
            remaining = remaining - 1 if remaining else (2 if trigger else 0)
            assert int(state != "IDLE") == int(remaining != 0)
            assert state == {0: "IDLE", 1: "P2", 2: "P1"}[remaining]
    assert "Two full clock periods" in card(98)["answer"]["en"]


def test_valid_delay_matches_payload_delay_even_for_bubbles():
    for valid_inputs in itertools.product((0, 1), repeat=5):
        stage_one = stage_two = (0, None)
        history = []
        for value, valid in enumerate(valid_inputs):
            history.append((valid, value))
            stage_one, stage_two = (valid, value), stage_one
            expected = history[-2] if len(history) >= 2 else (0, None)
            assert stage_two == expected
    assert_in_both(99, "`2`")
    assert "matching update conditions" in card(99)["answer"]["en"]


def test_composed_state_has_four_reachable_pairs_and_requires_two_bits():
    reached = {(0, 0)}
    for size in range(1, 4):
        for bits in itertools.product((0, 1), repeat=size):
            reached.add((sum(bits) % 2, bits[-1]))
    assert reached == set(itertools.product((0, 1), repeat=2))
    assert math.ceil(math.log2(len(reached))) == 2
    assert_in_both(100, "`2`")
