"""Independently check the short hardware exercises, including the diagrams.

These checks establish circuit/sequence correctness. They do not constitute
human editorial approval of this newly authored teaching material.
"""

import ast
import itertools
import json
import re
from collections import Counter
from pathlib import Path

CONTENT = (
    Path(__file__).resolve().parents[2]
    / "apps/web/src/content/fundamentals-hardware.json"
)
CARDS = json.loads(CONTENT.read_text(encoding="utf-8"))
BY_ID = {card["id"]: card for card in CARDS}


def card(number):
    return BY_ID[f"quick-hw-{number:02d}"]


def assert_in_answers(number, fragment):
    for language in ("he", "en"):
        assert fragment in card(number)["answer"][language], (number, language, fragment)


def truth_rows(number, language="en"):
    return [
        tuple(int(cell.strip()) for cell in line.strip("|").split("|"))
        for line in card(number)["answer"][language].splitlines()
        if re.fullmatch(r"\|(?:\s*[01]\s*\|){2,4}", line)
    ]


def boolean_expression(text, values):
    """Evaluate the actual authored Boolean formula using a restricted AST."""
    for source, target in (("AND", "and"), ("OR", "or"), ("NOT", "not"), ("XOR", "^")):
        text = re.sub(rf"\b{source}\b", target, text)
    tree = ast.parse(text.strip(), mode="eval")

    def walk(node):
        if isinstance(node, ast.Name):
            return bool(values[node.id])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not walk(node.operand)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            return all(walk(value) for value in node.values)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            return any(walk(value) for value in node.values)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitXor):
            return walk(node.left) != walk(node.right)
        raise AssertionError(f"Unsupported authored expression: {ast.dump(node)}")

    return int(walk(tree.body))


def backticks(number, language="en"):
    return re.findall(r"`([^`]+)`", card(number)["answer"][language])


def answer_sequence(number, *, arrows=False):
    for expression in backticks(number):
        separator = " → " if arrows else ", "
        if separator in expression:
            return expression.split(separator)
    raise AssertionError(f"No answer sequence found for {number}")


def fsm_table(number):
    diagram = card(number)["diagram"]
    result = {}
    for transition in diagram["transitions"]:
        label = transition["label"]
        if label in ("any p", "any x"):
            inputs = ["0", "1"]
            output = None
        elif "=" in label:
            inputs = label.split("=", 1)[1].split("/")
            output = None
        else:
            input_value, output = label.split("/")
            inputs = [input_value]
            output = int(output)
        for value in inputs:
            key = (transition["from"], int(value))
            assert key not in result, (number, key)
            result[key] = (transition["to"], output)
    assert set(result) == set(itertools.product(diagram["states"], (0, 1)))
    return result


def run_fsm(number, inputs):
    table = fsm_table(number)
    state = card(number)["diagram"]["initial"]
    states, outputs = [], []
    for value in inputs:
        state, output = table[(state, value)]
        states.append(state)
        outputs.append(output)
    return states, outputs


def test_scope_bilingual_shortness_and_diagram_contract():
    assert [item["id"] for item in CARDS] == [f"quick-hw-{n:02d}" for n in range(1, 61)]
    assert Counter(item["topic"] for item in CARDS) == {
        "gates": 16, "bits": 14, "sequential": 15, "states": 15,
    }
    assert sum("diagram" in item for item in CARDS) == 18
    for item in CARDS:
        assert set(item) <= {
            "id", "topic", "title", "prompt", "answer", "takeaway", "code", "diagram",
        }
        for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
            assert set(item[field]) == {"he", "en"}
            for language, text in item[field].items():
                assert text.strip() and len(text.split()) <= limit, (item["id"], field, language)
        if "code" in item:
            assert len(item["code"]["text"].splitlines()) <= 5
        if item.get("diagram", {}).get("kind") == "fsm":
            diagram = item["diagram"]
            assert 1 <= len(diagram["states"]) <= 3
            assert diagram["initial"] in diagram["states"]
            assert len(diagram["transitions"]) <= 6
            pairs = set()
            for transition in diagram["transitions"]:
                assert transition["from"] in diagram["states"]
                assert transition["to"] in diagram["states"]
                assert len(transition["label"]) <= 12
                pair = (transition["from"], transition["to"])
                assert pair not in pairs, (item["id"], pair)
                pairs.add(pair)
    for language in ("he", "en"):
        prompts = [item["prompt"][language] for item in CARDS]
        assert len(set(prompts)) == len(prompts)


def test_gate_truth_tables_and_drawn_gate_names():
    oracles = {
        1: ("AND", lambda a, b: int(a + b == 2)),
        2: ("OR", lambda a, b: int(a + b >= 1)),
        3: ("XOR", lambda a, b: int(a + b == 1)),
    }
    for number, (gate, oracle) in oracles.items():
        expected = [(a, b, oracle(a, b)) for a, b in itertools.product((0, 1), repeat=2)]
        assert truth_rows(number) == expected
        assert truth_rows(number, "he") == expected
        assert card(number)["diagram"] == {
            "kind": "gate", "gate": gate, "inputs": ["A", "B"], "output": "Y",
        }
    assert truth_rows(4) == truth_rows(4, "he") == [(0, 1), (1, 0)]
    assert card(4)["diagram"] == {
        "kind": "gate", "gate": "NOT", "inputs": ["A"], "output": "Y",
    }


def test_mux_uses_selected_data_not_selector_value():
    values = dict(re.findall(r"\b(D0|D1|S)=([01])", card(5)["prompt"]["en"]))
    selected = "D" + values["S"]
    expected = int(values[selected])
    assert expected != int(values["S"]), "The example must expose the common misconception."
    assert_in_answers(5, f"Y={selected}={expected}")
    assert card(5)["diagram"] == {
        "kind": "gate", "gate": "MUX", "inputs": ["D0", "D1", "S"], "output": "Y",
    }


def test_de_morgan_formula_exhaustively():
    left, right = backticks(6)[0].split(" = ")
    for a, b in itertools.product((0, 1), repeat=2):
        values = {"A": a, "B": b}
        expected = int(a + b < 2)
        assert boolean_expression(left, values) == expected
        assert boolean_expression(right, values) == expected
    assert backticks(6, "he") == backticks(6)


def test_majority_formula_exhaustively():
    formula = backticks(7)[0].removeprefix("Y=")
    for bits in itertools.product((0, 1), repeat=3):
        assert boolean_expression(formula, dict(zip("ABC", bits, strict=True))) == int(sum(bits) >= 2)
    assert backticks(7, "he") == backticks(7)


def test_absorption_formula_does_not_depend_on_b():
    left, right = backticks(8)[0].split(" = ")
    for a, b in itertools.product((0, 1), repeat=2):
        values = {"A": a, "B": b}
        assert boolean_expression(left, values) == boolean_expression(right, values) == a
    assert backticks(8, "he") == backticks(8)


def test_four_bit_unsigned_range():
    values = [int("".join(bits), 2) for bits in itertools.product("01", repeat=4)]
    assert_in_answers(9, f"`{min(values)}..{max(values)}`")
    assert_in_answers(9, f"`{len(set(values))}`")


def test_four_bit_overflow_and_carry():
    full = int("1111", 2) + int("0001", 2)
    assert_in_answers(10, f"`{full & 0b1111:04b}`")
    assert_in_answers(10, f"`{full:b}`")
    assert full >> 4 == 1


def test_eight_bit_shift():
    original = int(re.search(r"\b[01]{8}\b", card(11)["prompt"]["en"])[0], 2)
    result = (original << 1) & 255
    assert result == original * 2
    assert_in_answers(11, f"`{result:08b}`")
    for value in (original, result):
        assert_in_answers(11, str(value))


def test_bit_mask_targets_the_requested_position():
    expression = backticks(12)[1]
    value, mask, result = re.fullmatch(r"([01]{8}) AND ([01]{8}) = ([01]{8})", expression).groups()
    assert int(mask, 2) == 2**2
    assert int(result, 2) == int(value, 2) & int(mask, 2) == 0
    assert (int(value, 2) // 2**2) % 2 == 0
    assert backticks(12, "he") == backticks(12)


def test_set_and_clear_leave_other_bits_unchanged():
    for expression, position, wanted in zip(backticks(13), (3, 4), (1, 0), strict=True):
        original, operator, mask, result = re.fullmatch(
            r"([01]{8}) (OR|AND) ([01]{8}) = ([01]{8})", expression,
        ).groups()
        before, operand, after = int(original, 2), int(mask, 2), int(result, 2)
        expected = before | operand if operator == "OR" else before & operand
        assert after == expected
        assert (after >> position) & 1 == wanted
        assert (before ^ after) & ~(1 << position) == 0
        assert before == 0b01010000, "The two operations are independent."
    assert backticks(13, "he") == backticks(13)


def test_three_bit_parity_formula_and_examples():
    formula = backticks(14)[0].removeprefix("Y=")
    for bits in itertools.product((0, 1), repeat=3):
        assert boolean_expression(formula, dict(zip("ABC", bits, strict=True))) == sum(bits) % 2
    for example in backticks(14)[1:]:
        bits, result = example.split(" → ")
        assert int(result) == sum(map(int, bits)) % 2
    assert backticks(14, "he") == backticks(14)


def test_d_flip_flop_changes_only_at_the_sampling_edge():
    q = 0
    d = 1
    observed = []
    for is_rising_edge in (False, True):
        if is_rising_edge:
            q = d
        observed.append(q)
    assert backticks(15) == [f"Q={q}" for q in observed]
    assert backticks(15, "he") == backticks(15)


def test_two_flip_flops_use_old_state_simultaneously():
    q1 = q2 = 0
    sequence = [f"{q1}{q2}"]
    for _ in range(2):
        q1, q2 = 1, q1
        sequence.append(f"{q1}{q2}")
    assert answer_sequence(16, arrows=True) == sequence
    assert backticks(16, "he") == backticks(16)


def test_t_flip_flop_toggles_for_one():
    q = 0
    observed = []
    for _ in range(4):
        q ^= 1
        observed.append(str(q))
    assert answer_sequence(17) == observed
    assert backticks(17, "he") == backticks(17)


def test_t_flip_flop_zero_holds_instead_of_clearing():
    q = 1
    observed = []
    for _ in range(3):
        q ^= 0
        observed.append(str(q))
    assert answer_sequence(18) == observed
    assert backticks(18, "he") == backticks(18)


def test_synchronous_reset_has_priority_over_enable():
    values = {
        key: int(value, 2)
        for key, value in re.findall(r"\b(Q|D|EN|rst)=([01]+)", card(19)["prompt"]["en"])
    }
    q = 0 if values["rst"] else (values["D"] if values["EN"] else values["Q"])
    assert_in_answers(19, f"`Q={q:02b}`")
    assert values["EN"] == 0 and values["Q"] != q


def test_reset_timing_explanation_distinguishes_between_edge_and_no_edge():
    sync_q = async_q = 1
    reset = True
    if reset:
        async_q = 0
    assert (sync_q, async_q) == (1, 0)
    if reset:  # The next active clock edge.
        sync_q = 0
    assert (sync_q, async_q) == (0, 0)
    answer = card(20)["answer"]["en"]
    assert "without waiting for the clock" in answer
    assert "stays at 1 until the next active edge" in answer
    assert "if rst is still 1" in answer


def test_two_bit_counter_wraps_at_four_values():
    value = 0
    observed = []
    for _ in range(5):
        value = (value + 1) % (2**2)
        observed.append(f"{value:02b}")
    assert answer_sequence(21) == observed
    assert backticks(21, "he") == backticks(21)


def test_d_feedback_matches_toggling():
    q = 0
    observed = [str(q)]
    for _ in range(3):
        q = int(not q)
        observed.append(str(q))
    assert answer_sequence(22, arrows=True) == observed
    assert backticks(22, "he") == backticks(22)


def test_toggle_fsm_complete_diagram_and_answer():
    for inputs in itertools.product((0, 1), repeat=5):
        states, _ = run_fsm(23, inputs)
        expected = ["ON" if sum(inputs[:i]) % 2 else "OFF" for i in range(1, 6)]
        assert states == expected
    assert answer_sequence(23) == run_fsm(23, [1, 0, 1])[0]
    assert backticks(23, "he") == backticks(23)


def test_rising_transition_fsm_diagram_against_adjacent_input_pairs():
    for inputs in itertools.product((0, 1), repeat=5):
        states, outputs = run_fsm(24, inputs)
        expected = [
            int(current == 1 and previous == 0)
            for previous, current in zip((0, *inputs), inputs, strict=False)
        ]
        assert outputs == expected
        assert states == ["HIGH" if value else "LOW" for value in inputs]
    assert list(map(int, answer_sequence(24))) == run_fsm(24, [1, 1, 0, 1])[1]
    assert backticks(24, "he") == backticks(24)


def test_stream_parity_fsm_diagram_against_counted_ones():
    for inputs in itertools.product((0, 1), repeat=5):
        states, _ = run_fsm(25, inputs)
        expected = ["ODD" if sum(inputs[:i]) % 2 else "EVEN" for i in range(1, 6)]
        assert states == expected
    assert answer_sequence(25) == run_fsm(25, [1, 0, 1, 1])[0]
    assert backticks(25, "he") == backticks(25)


def test_two_consecutive_ones_answer_counts_trailing_run():
    inputs = [1, 0, 1, 1, 0]
    trailing_ones = 0
    expected = []
    for value in inputs:
        trailing_ones = trailing_ones + 1 if value else 0
        expected.append(int(trailing_ones >= 2))
    assert list(map(int, answer_sequence(26))) == expected
    assert backticks(26, "he") == backticks(26)


def test_sticky_event_fsm_diagram_against_any_prior_event():
    for inputs in itertools.product((0, 1), repeat=5):
        states, _ = run_fsm(27, inputs)
        expected = ["SET" if any(inputs[:i]) else "WAIT" for i in range(1, 6)]
        assert states == expected
    states, _ = run_fsm(27, [0, 1, 0])
    assert list(map(int, answer_sequence(27))) == [int(state == "SET") for state in states]
    assert backticks(27, "he") == backticks(27)


def test_mealy_example_really_depends_on_current_input():
    def output(ready, x):
        return int(ready and x)

    assert output(True, 0) != output(True, 1)
    assert output(False, 0) == output(False, 1)
    for answer in card(28)["answer"].values():
        assert "Mealy" in answer and "Moore" in answer
    assert "without a state transition" in card(28)["answer"]["en"]


def test_minimal_state_bits_and_unused_code():
    number_of_states = 3
    bits = 0
    while 2**bits < number_of_states:
        bits += 1
    unused = 2**bits - number_of_states
    assert backticks(29) == backticks(29, "he") == [str(bits), str(unused)]


def test_three_state_cycle_diagram_and_edge_count():
    diagram = card(30)["diagram"]
    transitions = {item["from"]: item["to"] for item in diagram["transitions"]}
    assert set(transitions) == set(diagram["states"])
    assert all(item["label"] == "tick" for item in diagram["transitions"])
    state = diagram["initial"]
    observed = []
    for index in range(1, 10):
        state = transitions[state]
        assert state == f"S{index % 3}"
        observed.append(state)
    assert answer_sequence(30) == observed[:5]
    assert backticks(30)[0] == observed[4]
    assert backticks(30, "he") == backticks(30)


def mux_connections(number):
    return dict(assignment.split("=") for assignment in backticks(number)[0].split(", "))


def run_authored_mux(number, values):
    values = {**values, "0": 0, "1": 1}
    connections = mux_connections(number)
    selector = values[connections["S"]]
    selected_data = connections[f"D{selector}"]
    return values[selected_data]


def assert_same_backticks(number):
    assert backticks(number, "he") == backticks(number)


def test_nand_nor_and_xnor_tables_and_formulas():
    oracles = {
        31: lambda a, b: int(a + b != 2),
        32: lambda a, b: int(a + b == 0),
        33: lambda a, b: int(a == b),
    }
    for number, oracle in oracles.items():
        expected = [(a, b, oracle(a, b)) for a, b in itertools.product((0, 1), repeat=2)]
        assert truth_rows(number) == truth_rows(number, "he") == expected
        if number in (32, 33):
            formula = backticks(number)[0].removeprefix("Y=")
            for a, b in itertools.product((0, 1), repeat=2):
                assert boolean_expression(formula, {"A": a, "B": b}) == oracle(a, b)
            assert_same_backticks(number)


def test_mux_realizations_for_not_and_and_or():
    for a, b in itertools.product((0, 1), repeat=2):
        values = {"A": a, "B": b}
        assert run_authored_mux(34, values) == int(a == 0)
        assert run_authored_mux(35, values) == int(a + b == 2)
        assert run_authored_mux(36, values) == int(a + b >= 1)
    for number in (34, 35, 36):
        connections = mux_connections(number)
        assert card(number)["diagram"] == {
            "kind": "gate", "gate": "MUX",
            "inputs": [f"{pin}={connections[pin]}" for pin in ("D0", "D1", "S")], "output": "Y",
        }
        assert_same_backticks(number)


def test_two_and_three_inversions():
    left, right = backticks(37)[0].split(" = ")
    third = backticks(37)[1]
    for a in (0, 1):
        assert boolean_expression(left, {"A": a}) == boolean_expression(right, {"A": a}) == a
        assert boolean_expression(third, {"A": a}) == 1 - a
    assert_same_backticks(37)


def test_distributive_factorization_for_all_eight_inputs():
    left, right = backticks(38)[0].split(" = ")
    for bits in itertools.product((0, 1), repeat=3):
        values = dict(zip("ABC", bits, strict=True))
        expected = int(bits[0] == 1 and sum(bits[1:]) >= 1)
        assert boolean_expression(left, values) == boolean_expression(right, values) == expected
    assert_same_backticks(38)


def test_evenness_is_determined_by_low_bit():
    for value in range(256):
        assert (value & 1) == value % 2
    example = int(backticks(39)[0], 2)
    assert example % 2 == 1
    assert "odd" in card(39)["answer"]["en"]
    assert "אי־זוגי" in card(39)["answer"]["he"]
    assert_same_backticks(39)


def test_binary_to_decimal_uses_the_set_bit_weights():
    expression, result = backticks(40)[0].split("=")
    original = re.search(r"\b[01]{5}\b", card(40)["prompt"]["en"])[0]
    weights = [2**index for index, bit in enumerate(reversed(original)) if bit == "1"]
    assert sorted(map(int, expression.split("+"))) == sorted(weights)
    assert int(result) == sum(weights) == int(original, 2)
    assert_same_backticks(40)


def test_decimal_to_binary_has_the_requested_width_and_value():
    expression, binary = backticks(41)
    original, expansion = expression.split("=")
    assert int(original) == sum(map(int, expansion.split("+"))) == int(binary, 2)
    assert int(original) == 37 and len(binary) == 6
    assert_same_backticks(41)


def test_twos_complement_interpretation_changes_the_top_weight():
    original = int("1110", 2)
    unsigned, signed = backticks(42)
    for expression, expected in ((unsigned, original), (signed, original - 2**4)):
        weights, result = expression.split("=")
        assert sum(map(int, weights.split("+"))) == int(result) == expected
    assert_same_backticks(42)


def test_sign_extension_preserves_signed_value():
    before, after = backticks(43)[0].split(" → ")

    def signed_value(bits):
        value = int(bits, 2)
        return value - 2 ** len(bits) if bits[0] == "1" else value

    assert len(before) == 4 and len(after) == 6
    assert after == before[0] * 2 + before
    assert signed_value(before) == signed_value(after) == -6
    expression, result = backticks(43)[1].split("=")
    assert sum(map(int, expression.split("+"))) == int(result) == signed_value(after)
    assert_same_backticks(43)


def test_one_hot_example_requires_exactly_one_set_bit():
    examples = backticks(44)
    assert [word.count("1") for word in examples] == [1, 0, 2]
    assert "Only" in card(44)["answer"]["en"]
    assert_same_backticks(44)


def test_full_adder_carry_and_sum_are_distinct_result_bits():
    inputs = dict(re.findall(r"\b(A|B|Cin)=([01])", card(45)["prompt"]["en"]))
    total = sum(map(int, inputs.values()))
    expected_carry, expected_sum = divmod(total, 2)
    assert_in_answers(45, f"`{total:b}`")
    assert_in_answers(45, f"`Cout={expected_carry}, S={expected_sum}`")
    assert_same_backticks(45)


def test_logical_and_arithmetic_right_shift_insert_different_bits():
    original = int(re.search(r"\b[01]{8}\b", card(46)["prompt"]["en"])[0], 2)
    logical = original // 2
    arithmetic = (original // 2) | (original & 128)
    assert backticks(46) == [f"{logical:08b}", f"{arithmetic:08b}"]
    assert_same_backticks(46)


def test_mux_enable_holds_or_loads_for_all_input_cases():
    for en, q, data in itertools.product((0, 1), repeat=3):
        assert run_authored_mux(47, {"EN": en, "Q": q, "data": data}) == (data if en else q)
    connections = mux_connections(47)
    assert card(47)["diagram"] == {
        "kind": "gate", "gate": "MUX",
        "inputs": [f"{pin}={connections[pin]}" for pin in ("D0", "D1", "S")], "output": "Y",
    }
    assert_same_backticks(47)


def test_enabled_counter_sequence():
    current = int("011", 2)
    observed = []
    for enabled in (1, 0, 1, 1):
        if enabled:
            current = (current + 1) % 8
        observed.append(f"{current:03b}")
    assert answer_sequence(48) == observed
    assert_same_backticks(48)


def test_unsigned_decrement_wraps_from_zero():
    expected = (0 - 1) % 2**3
    assert backticks(49) == [f"{expected:03b}", str(expected)]
    assert_same_backticks(49)


def test_active_low_synchronous_reset_overrides_enabled_data():
    values = {
        key: int(value)
        for key, value in re.findall(r"\b(Q|data|EN|rst_n)=([01])", card(50)["prompt"]["en"])
    }
    result = 0 if not values["rst_n"] else (values["data"] if values["EN"] else values["Q"])
    assert values["EN"] == values["data"] == values["Q"] == 1
    assert_in_answers(50, f"`Q={result}`")


def test_uninitialized_d_flip_flop_becomes_known_after_valid_sampling():
    possible_before = {0, 1}
    possible_after = {1 for _previous in possible_before}
    assert len(possible_before) > 1 and possible_after == {1}
    assert backticks(51) == [f"Q={next(iter(possible_after))}"]
    assert "guarantees no particular Q value" in card(51)["answer"]["en"]
    assert_same_backticks(51)


def test_counter_bit_traces_and_division_ratios():
    for expression, bit in zip(backticks(52), (0, 1), strict=True):
        label, values = expression.split(": ")
        assert label == f"Q{bit}"
        assert list(map(int, values.split(","))) == [(count >> bit) & 1 for count in range(1, 5)]
        cycle = [((count % 8) >> bit) & 1 for count in range(8)]
        period = 2 ** (bit + 1)
        assert cycle[:period] == cycle[period:2 * period]
    assert_same_backticks(52)


def test_single_sample_pulse_advances_one_pipeline_stage_per_edge():
    q1 = q2 = q3 = 0
    observed = []
    for value in (1, 0, 0, 0):
        q1, q2, q3 = value, q1, q2
        observed.append(f"{q1}{q2}{q3}")
    assert answer_sequence(53) == observed
    assert_same_backticks(53)


def test_ready_busy_diagram_uses_only_the_input_relevant_to_each_state():
    diagram = card(54)["diagram"]
    table = {}
    for transition in diagram["transitions"]:
        signal, value = transition["label"].split("=")
        assert signal == ("r" if transition["from"] == "READY" else "d")
        table[(transition["from"], int(value))] = transition["to"]
    assert set(table) == set(itertools.product(diagram["states"], (0, 1)))
    pairs = list(itertools.product((0, 1), repeat=2))
    for inputs in itertools.product(pairs, repeat=4):
        state = expected = "READY"
        for request, done in inputs:
            relevant_input = request if state == "READY" else done
            state = table[(state, relevant_input)]
            if expected == "READY" and request:
                expected = "BUSY"
            elif expected == "BUSY" and done:
                expected = "READY"
            assert state == expected
    state = "READY"
    observed = []
    for request, done in ((1, 0), (1, 0), (0, 1)):
        state = table[(state, request if state == "READY" else done)]
        observed.append(state)
    assert answer_sequence(54) == observed
    assert_same_backticks(54)


def test_two_coin_dispenser_diagram_matches_cumulative_coin_count():
    for inputs in itertools.product((0, 1), repeat=5):
        states, outputs = run_fsm(55, inputs)
        expected_states = ["ONE" if sum(inputs[:i]) % 2 else "EMPTY" for i in range(1, 6)]
        expected_outputs = [
            int(sum(inputs[:i]) // 2 > sum(inputs[:i - 1]) // 2) for i in range(1, 6)
        ]
        assert states == expected_states
        assert outputs == expected_outputs
    assert list(map(int, answer_sequence(55))) == run_fsm(55, [1, 0, 1, 1])[1]
    assert_same_backticks(55)


def test_error_state_is_unreachable_by_graph_search():
    table = fsm_table(56)
    reached = {card(56)["diagram"]["initial"]}
    pending = list(reached)
    while pending:
        state = pending.pop()
        for value in (0, 1):
            target, _ = table[(state, value)]
            if target not in reached:
                reached.add(target)
                pending.append(target)
    assert reached == {"IDLE", "RUN"}
    assert "ERROR" not in reached
    assert "unreachable" in card(56)["answer"]["en"]
    assert "לא נגיש" in card(56)["answer"]["he"]


def test_one_hot_state_encoding_has_one_flip_flop_per_state():
    count, codes = backticks(57)
    words = codes.split(", ")
    assert int(count) == len(words) == 3
    assert len(set(words)) == 3
    assert all(len(word) == 3 and word.count("1") == 1 for word in words)
    assert_same_backticks(57)


def test_priority_transitions_are_complete_exclusive_and_prioritize_a():
    expressions = dict(item.split("=", 1) for item in backticks(58))
    for a, b in itertools.product((0, 1), repeat=2):
        values = {"a": a, "b": b}
        actual = {name: boolean_expression(formula, values) for name, formula in expressions.items()}
        assert sum(actual.values()) == 1
        expected_name = "to_A" if a else ("to_B" if b else "stay")
        assert actual[expected_name] == 1
    assert_same_backticks(58)


def test_overlapping_eleven_detector_diagram_retains_latest_one():
    for inputs in itertools.product((0, 1), repeat=5):
        states, outputs = run_fsm(59, inputs)
        expected = [int(previous == current == 1) for previous, current in zip((0, *inputs), inputs, strict=False)]
        assert outputs == expected
        assert states == ["ONE" if value else "ZERO" for value in inputs]
    assert list(map(int, answer_sequence(59))) == run_fsm(59, [1, 1, 1, 0, 1])[1]
    assert_same_backticks(59)


def test_unused_counter_code_recovers_to_a_valid_state():
    source, target = backticks(60)[0].split(" → ")
    next_state = {"00": "01", "01": "10", "10": "00", source: target}
    assert set(next_state) == {"00", "01", "10", "11"}
    assert target == "00"
    valid_states = {"00", "01", "10"}
    assert all(next_state[state] in valid_states for state in next_state)
    assert_same_backticks(60)
