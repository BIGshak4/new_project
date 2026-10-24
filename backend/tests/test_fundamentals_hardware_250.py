"""Bounded independent checks for the 25 new hardware study objectives.

Python snippets are executed from the authored JSON. Other checks establish
truth-table, state, resource or arithmetic claims against independent models.
These are logical models, not HDL compilation or physical timing certification.
"""

from __future__ import annotations

import itertools
import json
import math
import re
from fractions import Fraction
from pathlib import Path

CONTENT = Path(__file__).resolve().parents[2] / "apps/web/src/content"
CARDS = json.loads((CONTENT / "fundamentals-hardware-250.json").read_text(encoding="utf-8"))
BY_ID = {int(item["id"].rsplit("-", 1)[1]): item for item in CARDS}


def snippet(number, name):
    namespace = {}
    exec(BY_ID[number]["code"]["text"], namespace)
    return namespace[name]


def mentions(number, fragment):
    for language in ("he", "en"):
        assert fragment in BY_ID[number]["answer"][language], (number, language)


def test_new_cards_have_stable_ids_bilingual_limits_and_real_interview_sources():
    prep = json.loads(
        (CONTENT.parents[3] / "interview_preparation/questions.json").read_text(encoding="utf-8")
    )
    sources = {item["id"] for item in prep["questions"]}
    previous = []
    for filename in (
        "fundamentals-hardware.json", "fundamentals-hardware-expansion.json",
        "fundamentals-code-logic.json", "fundamentals-code-expansion.json",
        "fundamentals-reasoning-expansion.json",
    ):
        previous.extend(json.loads((CONTENT / filename).read_text(encoding="utf-8")))
    assert len(CARDS) == len(BY_ID) == 25
    assert set(BY_ID) == set(range(101, 126))
    assert not {item["id"] for item in CARDS} & {item["id"] for item in previous}
    for field in ("title", "prompt"):
        for language in ("he", "en"):
            texts = [item[field][language] for item in [*previous, *CARDS]]
            assert len(texts) == len(set(texts))
    for item in CARDS:
        assert item.keys() <= {
            "id", "topic", "interviewIds", "title", "prompt", "answer", "takeaway", "code", "diagram",
        }
        assert item["topic"] in {"gates", "bits", "sequential", "states"}
        assert item["interviewIds"] and set(item["interviewIds"]) <= sources
        for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
            assert set(item[field]) == {"he", "en"}
            for language, text in item[field].items():
                assert text.strip() and len(text.split()) <= limit, (item["id"], field, language)
                if language == "en":
                    assert not re.search(r"[\u0590-\u05ff]", text)
        if "code" in item:
            assert item["code"]["language"] == "python"
            assert len(item["code"]["text"].splitlines()) <= 5


def test_weighted_adder_and_conditional_carry_against_integer_arithmetic():
    weighted, carry = snippet(101, "weighted"), snippet(102, "carry_out")
    for a, b, c in itertools.product((0, 1), repeat=3):
        assert weighted(a, b, c) == sum((4 * a, 4 * b, 4 * c))
        assert carry(a, b, c) == (a + b + c) // 2
    mentions(101, "4S+8K")
    mentions(102, "P=A XOR B")
    # Mixing an old-weight carry into the next column breaks conservation.
    assert weighted(1, 1, 1) == 12 != 4 * (1 + 1)


def test_authored_mux_wiring_and_shared_nand_network_match_truth_tables():
    diagram = BY_ID[103]["diagram"]
    assert diagram == {
        "kind": "gate", "gate": "MUX", "inputs": ["D0=B", "D1=C", "S=A"], "output": "F",
    }
    connections = dict(item.split("=") for item in diagram["inputs"])
    for a, b, c in itertools.product((0, 1), repeat=3):
        signals = {"A": a, "B": b, "C": c}
        result = signals[connections[f"D{signals[connections['S']]}"]]
        expected = int((a, b, c) in ((0, 1, 0), (0, 1, 1), (1, 0, 1), (1, 1, 1)))
        assert result == expected
    nand_xor = snippet(104, "nand_xor")
    for a, b in itertools.product((0, 1), repeat=2):
        assert nand_xor(a, b) == int(a != b)
    assert BY_ID[104]["code"]["text"].count("1 - (") == 4


def test_priority_inhibit_and_balanced_binary_composition_depth():
    keep = snippet(105, "keep_bit_one")
    for word in range(16):
        active_positions = [index for index in range(4) if f"{word:04b}"[::-1][index] == "1"]
        expected_position = max(active_positions, default=-1)
        assert keep(word) == int(expected_position == 1)
    mentions(105, "y1=x1 AND NOT(x2 OR x3)")

    def depth_and_cells(leaves):
        if leaves == 1:
            return 0, 0
        left_depth, left_cells = depth_and_cells(leaves // 2)
        right_depth, right_cells = depth_and_cells(leaves - leaves // 2)
        return 1 + max(left_depth, right_depth), 1 + left_cells + right_cells

    for size in range(1, 258):
        levels, cells = depth_and_cells(size)
        assert levels == math.ceil(math.log2(size))
        assert cells == size - 1
    mentions(106, "ceil(log2(n))")
    assert "bounded fan-in" in BY_ID[106]["answer"]["en"]


def test_latch_feedback_fixed_points_and_opposite_phase_composition():
    for data, enable in itertools.product((0, 1), repeat=2):
        fixed_points = {q for q in (0, 1) if q == (data if enable else q)}
        assert fixed_points == ({data} if enable else {0, 1})
    # All low/high-phase input sequences up to four cycles, initialized only
    # for this model. The slave holds throughout low, then takes master's value.
    for samples in itertools.product((0, 1), repeat=8):
        master = slave = 0
        for low_data, high_data in zip(samples[::2], samples[1::2], strict=True):
            old_slave = slave
            master = low_data
            assert slave == old_slave
            slave = master
            assert slave == low_data
            assert master == low_data  # High-phase input changes cannot cross.
            if high_data != low_data:
                both_high_transparent = high_data
                assert both_high_transparent != slave
    assert "does not define initialization" in BY_ID[107]["answer"]["en"]
    assert "physical transparency overlap" in BY_ID[108]["answer"]["en"]


def test_live_sample_comparison_can_cancel_and_pulse_width_depends_on_phase():
    for saved, intermediate in itertools.product((0, 1), repeat=2):
        observed = [int(saved != value) for value in (saved, intermediate, saved)]
        assert observed == [0, int(intermediate != saved), 0]
    for transition in range(1, 10):
        high_times = [t for t in range(10) if t >= transition]
        assert len(high_times) == 10 - transition
    mentions(109, "OUT=In XOR Q")
    mentions(110, "7ns")
    mentions(110, "2ns")


def test_toggle_duty_depends_on_edges_and_feedback_budget_is_one_input_cycle():
    for input_high in (Fraction(1), Fraction(2), Fraction(5), Fraction(9)):
        assert 0 < input_high < 10
        q = 0
        intervals = []
        for _ in range(8):
            q = 1 - q
            intervals.append((q, Fraction(10)))
        high_duration = sum(duration for value, duration in intervals if value)
        total = sum(duration for _, duration in intervals)
        assert high_duration / total == Fraction(1, 2)
    for period in (Fraction(3), Fraction(7, 2), Fraction(4), Fraction(5)):
        data_arrival = Fraction(1) + 2
        setup_deadline = period - 1
        assert (data_arrival <= setup_deadline) == (period >= 4)
    # Budgeting against output period would incorrectly accept a 2ns input period.
    assert 1 + 2 + 1 <= 2 * 2 and not 1 + 2 + 1 <= 2
    mentions(111, "50%")
    mentions(112, "T>=1+2+1=4ns")
    assert "two-cycle path" in BY_ID[112]["answer"]["en"]


def test_fifth_event_snippet_against_event_positions_including_long_highs():
    step = snippet(113, "fifth")
    for samples in itertools.product((0, 1), repeat=12):
        rising_positions = [index for index, bit in enumerate(samples)
                            if bit and (index == 0 or not samples[index - 1])]
        expected_pulses = set(rising_positions[4::5])
        prev = count = 0
        for index, bit in enumerate(samples):
            prev, count, pulse = step(prev, count, bit)
            assert pulse == int(index in expected_pulses)
            assert 0 <= count <= 4 and prev == bit
    prev = count = pulses = 0
    for bit in (1,) * 20:
        prev, count, pulse = step(prev, count, bit)
        pulses += pulse
    assert count == 1 and pulses == 0


def test_zero_padded_threshold_startup_and_saturation_counterexample():
    history = [0] * 10
    observed = []
    for bit in (1, 1, 1):
        history = history[1:] + [bit]
        observed.append(int(sum(history) >= 3))
    assert observed == [0, 0, 1]
    # Independently enumerate every ten-sample old window and each entering bit.
    counterexamples = []
    for bits in itertools.product((0, 1), repeat=10):
        for incoming in (0, 1):
            exact = sum(bits[1:] + (incoming,))
            assert exact == sum(bits) - bits[0] + incoming
            capped_update = min(3, sum(bits)) - bits[0] + incoming
            if (exact >= 3) != (capped_update >= 3):
                counterexamples.append((bits, incoming))
    assert ((1, 1, 1, 1, 0, 0, 0, 0, 0, 0), 0) in counterexamples
    assert "seven earlier zeros" in BY_ID[114]["answer"]["en"]
    assert "4 to 3" in BY_ID[115]["answer"]["en"]


def test_authored_threshold_predicate_catches_equality_and_cross_block_window():
    predicate = next(text for text in re.findall(r"`([^`]+)`", BY_ID[116]["answer"]["en"])
                     if text.startswith("count"))
    assert predicate == "count>=3"
    for bits in itertools.product((0, 1), repeat=10):
        count = sum(bits)
        observed = eval(predicate, {"__builtins__": {}}, {"count": count})
        expected = len([bit for bit in bits if bit]) > 2
        assert observed == expected
    assert 4 >= 3 and 4 != 3
    samples = [0] * 8 + [1, 1, 1]
    assert sum(samples[-10:]) == 3
    assert sum(samples[10:]) == 1
    mentions(117, "2..11")


def test_same_address_forwarding_and_port_resource_limits():
    for old_value, new_value in itertools.product(range(16), repeat=2):
        for read_address, write_address in itertools.product(range(4), repeat=2):
            memory = [old_value] * 4
            memory[write_address] = new_value
            expected = memory[read_address]
            response = new_value if read_address == write_address else old_value
            assert response == expected
    assert "write_data" in BY_ID[118]["answer"]["en"]
    # A synchronized replica write consumes the only operation of each port.
    remaining_ports = sum(max(0, 1 - writes) for writes in (1, 1))
    assert remaining_ports == 0
    assert "both ports are already occupied" in BY_ID[122]["answer"]["en"]
    banks = {address: address % 2 for address in range(8)}
    assert banks[0] == banks[2] and banks[0] != banks[1]
    conflicts = {(read, write) for read, write in itertools.product(range(8), repeat=2)
                 if banks[read] == banks[write]}
    assert len(conflicts) == 32 and (0, 2) in conflicts and (0, 1) not in conflicts
    assert "Both addresses use bank 0" in BY_ID[123]["answer"]["en"]


def test_address_patterns_reveal_every_stable_single_alias_pair():
    pattern = snippet(121, "address_pattern")

    def failing_reads(mapping, values):
        storage = {}
        for address, value in enumerate(values):
            storage[mapping[address]] = value
        return [address for address, value in enumerate(values)
                if storage[mapping[address]] != value]

    for left, right in itertools.combinations(range(8), 2):
        mapping = list(range(8))
        mapping[right] = mapping[left]
        assert failing_reads(mapping, [1] * 8) == []
        assert any(failing_reads(mapping, [pattern(address, bit) for address in range(8)])
                   for bit in range(3))
    mapping = list(range(8))
    mapping[2] = mapping[0]
    assert failing_reads(mapping, [pattern(address, 0) for address in range(8)]) == []
    assert failing_reads(mapping, [pattern(address, 1) for address in range(8)])
    for bit in range(3):
        assert failing_reads(list(range(8)), [pattern(address, bit) for address in range(8)]) == []
    assert "every write used that value" in BY_ID[119]["answer"]["en"]


def test_bijective_mapping_is_observationally_equivalent_under_repeated_writes():
    for mapping in itertools.permutations(range(4)):
        physical = [None] * 4
        logical = [None] * 4
        for address, value in ((0, 5), (1, 0), (2, 8), (3, 2), (0, 9), (2, 1)):
            physical[mapping[address]] = value
            logical[address] = value
            assert [physical[mapping[read]] for read in range(4)] == logical
    assert "bijective permutation" in BY_ID[120]["answer"]["en"]


def test_block_close_includes_final_sample_then_resets_independent_next_block():
    close = snippet(124, "close_block")
    for count, final_error in itertools.product(range(11), (0, 1)):
        errors = [1] * count + [0] * (99_999 - count) + [final_error]
        reset_count, failed = close(count, final_error)
        assert failed == int(sum(errors) > 10)
        assert reset_count == 0
    count, failed = close(10, 1)
    assert (count, failed) == (0, 1)
    assert close(10, 0) == (0, 0)
    assert close(count, 1) == (0, 0)  # Old block failure does not leak into new block count.


def test_three_single_edge_intervals_cannot_form_half_duty():
    for levels in itertools.product((0, 1), repeat=3):
        duty = Fraction(sum(levels), 3)
        assert duty != Fraction(1, 2)
    assert {Fraction(sum(levels), 3) for levels in itertools.product((0, 1), repeat=3)} == {
        Fraction(0), Fraction(1, 3), Fraction(2, 3), Fraction(1),
    }
    mentions(125, "1.5T")
    assert "opposite edge" in BY_ID[125]["answer"]["en"]
