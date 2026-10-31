"""Finite independent oracles for the nine owned 31 October hardware records."""

import importlib.util
import itertools
import random
from pathlib import Path

SOLUTIONS = Path(__file__).resolve().parents[1] / "solutions"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SOLUTIONS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check199():
    model = load("prep_199_rotate_right_mux")
    count = 0
    for width in (1, 2, 4, 8):
        for value in range(1 << width):
            for amount in range(width):
                word = f"{value:0{width}b}"
                expected = word[-amount:] + word[:-amount] if amount else word
                assert model.rotate_right(value, width, amount) == int(expected, 2)
                count += 1
    return {"status": "pass", "exhaustive_word_amount_pairs": count,
            "widths": [1, 2, 4, 8], "scope": "MUX Boolean stages versus independent string rotation; no HDL/timing test"}


def check200():
    model = load("prep_200_mux_logic_and_switches")
    for a, b, select in itertools.product((0, 1), repeat=3):
        expected = (1-select)*a + select*b
        assert model.gate_mux(a, b, select) == expected
        assert model.transmission_gate_mux(a, b, select) == expected
        level = model.nmos_pass_level(a, b, select)
        assert level == (0.75 if expected else 0)
    assert list(model.TRANSISTOR_COUNTS.values()) == [14, 6, 4, 2]
    return {"status": "pass", "binary_input_rows": 8,
            "scope": "Ideal switch connectivity and declared device counting; voltage cap is an illustrative model, not SPICE or noise-margin qualification"}


def check202():
    model = load("prep_202_enabled_mod_six_counter")
    for state, enable, reset in itertools.product(range(8), (0, 1), (False, True)):
        if reset or state in (6, 7):
            expected = 0
        elif enable:
            expected = (state + 1) % 6
        else:
            expected = state
        assert model.next_count(state, enable, reset) == expected
    state = 0
    for edge in range(1000):
        state = model.next_count(state, 1)
        assert state == (edge + 1) % 6
    return {"status": "pass", "transition_rows_including_reset": 32,
            "continuous_enable_edges": 1000, "scope": "Python transition model; proposed SystemVerilog not compiled"}


def suffix_oracle(bits, pattern, resets=()):
    history = ""
    output = []
    for edge, bit in enumerate(bits):
        history = "" if edge in resets else history + str(bit)
        output.append(int(history.endswith(pattern)))
    return output


def moore_distinguishability(transitions):
    pairs = 0
    for first, second in itertools.combinations(range(5), 2):
        distinguished = int(first == 4) != int(second == 4)
        for length in range(1, 5):
            for continuation in itertools.product((0, 1), repeat=length):
                left, right = first, second
                for bit in continuation:
                    left, right = transitions[left][bit], transitions[right][bit]
                    if (left == 4) != (right == 4):
                        distinguished = True
        assert distinguished
        pairs += 1
    return pairs


def check204():
    model = load("prep_204_sequence_1101")
    count = 0
    for length in range(13):
        for bits in itertools.product((0, 1), repeat=length):
            assert model.detect(bits) == suffix_oracle(bits, "1101")
            count += 1
    for bits in itertools.product((0, 1), repeat=8):
        assert model.detect(bits, (2, 5)) == suffix_oracle(bits, "1101", (2, 5))
    assert model.detect((1, 1, 0, 1, 1, 0, 1)) == [0, 0, 0, 1, 0, 0, 1]
    pairs = moore_distinguishability(model.TRANSITIONS)
    return {"status": "pass", "all_streams_through_length_12": count,
            "reset_streams": 256, "distinguished_moore_state_pairs": pairs,
            "scope": "Finite Moore model and suffix oracle; RTL not compiled"}


def check205():
    model = load("prep_205_cmos_inverter")
    for bit in (0, 1):
        row = model.rail_inverter(bit)
        assert row["pmos_on"] != row["nmos_on"]
        assert row["vout_bit"] == 1-bit and not row["ideal_dc_rail_path"]
    nmos, pmos = model.gate_overdrive_flags(0.5)
    assert nmos and pmos
    return {"status": "pass", "rail_input_rows": 2, "middle_voltage_conduction_example": True,
            "scope": "Ideal conduction flags only; no quantitative VTC, leakage, SPICE or physical timing validation"}


def check207():
    model = load("prep_207_sequence_0101_storage")
    count = 0
    for length in range(13):
        for bits in itertools.product((0, 1), repeat=length):
            expected = suffix_oracle(bits, "0101")
            assert model.detect_moore(bits) == expected
            assert model.detect_rolling_fifo(bits) == expected
            count += 1
    for bits in itertools.product((0, 1), repeat=8):
        expected = suffix_oracle(bits, "0101", (2, 5))
        assert model.detect_moore(bits, (2, 5)) == expected
        assert model.detect_rolling_fifo(bits, (2, 5)) == expected
    assert model.detect_moore((0, 1, 0, 1, 0, 1)) == [0, 0, 0, 1, 0, 1]
    assert model.detect_moore((0, 1, 0, 1))[-1] != model.detect_moore((0, 0, 0, 1))[-1]
    pairs = moore_distinguishability(model.TRANSITIONS)
    return {"status": "pass", "all_streams_through_length_12": count,
            "reset_streams": 256, "distinguished_moore_state_pairs": pairs,
            "scope": "FSM and explicitly stateful four-peek rolling FIFO; no storage-free serial implementation claimed"}


def check102():
    model = load("prep_102_push_pop_address_batch21")
    count = 0
    for mask, push, pop, data in itertools.product(range(16), (False, True), (None, -1, 0, 1, 2, 3, 4), (0, 15)):
        device = model.AddressMemory(4, 4)
        occupied = {a for a in range(4) if mask & (1 << a)}
        device.occupied = occupied.copy()
        valid_pop = pop in occupied
        remaining = occupied - {pop} if valid_pop else occupied.copy()
        available = sorted(set(range(4)) - remaining)
        address = available[0] if push and available else None
        if address is not None:
            remaining.add(address)
        actual = device.tick(push=push, data=data, pop_address=pop)
        assert actual == {"push_success": address is not None,
                          "push_address": address, "pop_success": valid_pop}
        assert device.occupied == remaining
        if address is not None:
            assert device.payload[address] == data
        count += 1
    device = model.AddressMemory()
    oracle = {}
    rng = random.Random(31)
    for _ in range(10000):
        push, data, pop = rng.randrange(2), rng.randrange(1 << 32), rng.randrange(-1, 33)
        reset = rng.randrange(100) == 0
        if reset:
            oracle.clear()
        else:
            oracle.pop(pop, None)
            free = next((a for a in range(32) if a not in oracle), None)
            if push and free is not None:
                oracle[free] = data
        device.tick(push=push, data=data, pop_address=pop, reset=reset)
        assert device.occupied == set(oracle)
        assert all(device.payload[a] == value for a, value in oracle.items())
    return {"status": "pass", "depth_four_one_edge_cases": count, "depth_32_seeded_edges": 10000,
            "scope": "Atomic pop-before-push model; no RAM macro timing or concurrent external clients"}


def check011():
    model = load("prep_011_mux_ambiguity_batch21")
    plain, complemented = [], []
    for a, b, c in itertools.product((0, 1), repeat=3):
        product = a*b*(1-c)
        assert model.plain_product(a, b, c) == product
        assert model.complemented_product(a, b, c) == 1-product
        plain.append(product)
        complemented.append(1-product)
    signals = [(a, b, c, 0, 1) for a, b, c in itertools.product((0, 1), repeat=3)]
    for select, first, second in itertools.product(range(5), repeat=3):
        truth = [model.mux(row[select], row[first], row[second]) for row in signals]
        assert truth != plain and truth != complemented
    return {"status": "pass", "both_truth_tables_rows": 16, "single_mux_choices_checked": 125,
            "scope": "Raw inputs/constants with ordinary MUX semantics; source negation ambiguity retained"}


def check094():
    model = load("prep_094_matrix_reverse_columns_batch21")
    count = 0
    for rows, cols in itertools.product(range(1, 4), range(1, 5)):
        for bits in itertools.product((0, 1), repeat=rows*cols):
            matrix = [list(bits[row*cols:(row+1)*cols]) for row in range(rows)]
            output = model.reverse_columns(matrix)
            assert output == [list(reversed(row)) for row in matrix]
            assert model.reverse_columns(output) == matrix
            for row in range(rows):
                for col in range(cols):
                    assert output[row][col] == bits[model.flat_wire_index(row, col, cols)]
            count += 1
    source = [[int(b) for b in row] for row in ("011101", "001111", "101100")]
    expected = [[int(b) for b in row] for row in ("101110", "111100", "001101")]
    assert model.reverse_columns(source) == expected
    return {"status": "pass", "exhaustive_rectangular_bit_matrices": count, "source_example": True,
            "scope": "Logical wire permutation and involution, not routed area/delay or serial memory throughput"}


CHECKS = {199: check199, 200: check200, 202: check202, 204: check204, 205: check205,
          207: check207, 102: check102, 11: check011, 94: check094}
