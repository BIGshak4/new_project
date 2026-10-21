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
        if label == "any p":
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
    assert [item["id"] for item in CARDS] == [f"quick-hw-{n:02d}" for n in range(1, 31)]
    assert Counter(item["topic"] for item in CARDS) == {
        "gates": 8, "bits": 6, "sequential": 8, "states": 8,
    }
    assert sum("diagram" in item for item in CARDS) == 10
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
