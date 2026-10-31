"""Independent finite oracles; run with Python 3.12 from any directory."""
import importlib.util
import itertools
import json
import hashlib
from pathlib import Path
import random

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('batch20_sequential', BASE / 'solutions/prep_216_220_sequential.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def run(write=True):
    counts = {}
    q0 = q1 = 0
    for cycle in range(1, 1025):
        q0, q1 = m.divider_step(q0, q1)
        assert q0 == cycle % 2 and q1 == (cycle // 2) % 2
    for state in itertools.product(range(2), repeat=2):
        assert m.divider_step(*state, reset=True) == (0, 0)
    counts['PREP-216'] = {'checked_cycles': 1024, 'reset_states': 4}

    detector_checks = 0
    for n in range(13):
        for bits in itertools.product(range(2), repeat=n):
            state = mealy = 0
            shift = m.ShiftDetector()
            history = ''
            for bit in bits:
                history += str(bit)
                expected = history.endswith('101101')
                state, a = m.moore_step(state, bit)
                mealy, b = m.mealy_step(mealy, bit)
                assert (a, b, shift.step(bit)) == (expected,) * 3
                detector_checks += 1
    state = 0
    positions = []
    for i, bit in enumerate(map(int, '101101101'), 1):
        state, hit = m.moore_step(state, bit)
        if hit:
            positions.append(i)
    assert positions == [6, 9]
    for state in range(7):
        assert m.moore_step(state, 0, reset=True) == (0, False)
        assert m.moore_step(state, 1, valid=False) == (state, state == 6)
    counts['PREP-217'] = {'binary_streams_lengths_0_through_12': 8191,
                         'prefix_comparisons_three_models': detector_checks,
                         'overlap_positions': positions}

    matcher_checks = 0
    stores = [()] + [(x,) for x in range(8)] + list(itertools.combinations_with_replacement(range(8), 2))
    for stored in stores:
        for pair in (False, True):
            for seq in itertools.product(range(8), repeat=3):
                dut = m.WordMatcher(stored, pair=pair, width=3)
                accepted = []
                for x in seq:
                    accepted.append(x)
                    expected = x in stored and (not pair or (len(accepted) > 1 and accepted[-2] in stored))
                    assert dut.step(x) == expected
                    assert dut.step(0, valid=False) is False
                    matcher_checks += 1
                assert dut.step(0, reset=True) is False
                assert dut.stored == ()
                assert dut.step(seq[-1]) is False
    rng = random.Random(218)
    stored = (0, (1 << 64) - 1)
    dut = m.WordMatcher(stored)
    for x in [0, (1 << 64) - 1, 1 << 63] + [rng.getrandbits(64) for _ in range(2000)]:
        assert dut.step(x) == (x in stored)
    # Exact representable-set lower bound, not a floating-point approximation.
    assert 1 + (1 << 64) + (1 << 64) * ((1 << 64) - 1) // 2 > (1 << 127)
    counts['PREP-218'] = {'exhaustive_three_value_prefix_checks_width3': matcher_checks,
                         'stored_sets_including_empty_and_duplicates': len(stores),
                         'width64_cases': 2003, 'invalid_cycles_skip': True}

    expression_checks = 0
    for width in (1, 2, 4):
        limit = min(4, 1 << width)
        mask = (1 << width) - 1
        for n in range(1, 6):
            for nums in itertools.product(range(limit), repeat=n):
                for ops in itertools.product(('+', '*'), repeat=n-1):
                    # Oracle materializes all multiplication runs, then sums.
                    terms = [nums[0]]
                    for op, value in zip(ops, nums[1:]):
                        if op == '*': terms[-1] *= value
                        else: terms.append(value)
                    expected = sum(terms) & mask
                    dut = m.InfixEvaluator(width)
                    tokens = [nums[0]]
                    for op, num in zip(ops, nums[1:]): tokens.extend([op, num])
                    tokens.append('=')
                    result = None
                    for token in tokens:
                        assert dut.step(None, valid=False) is None
                        result = dut.step(token)
                    assert result == expected
                    expression_checks += 1
    dut = m.InfixEvaluator(8)
    for token in (2, '+', 3, '*', 4): assert dut.step(token) is None
    assert dut.step('=') == 14
    for bad in (['='], ['*'], [1, 2], [1, '+', '='], [1, '*', '+']):
        dut.reset()
        try:
            for token in bad: dut.step(token)
        except ValueError:
            pass
        else:
            raise AssertionError(('accepted malformed expression', bad))
    dut.step(3); dut.step(None, reset=True)
    assert dut.step(0) is None and dut.step('=') == 0
    counts['PREP-219'] = {'exhaustive_expressions_widths_1_2_4': expression_checks,
                         'max_operands': 5, 'malformed_sequences': 5,
                         'precedence_counterexample_result': 14}

    memory_checks = 0
    for contents in itertools.product(range(2), repeat=4):
        for wr_addr, wr_data, wr_en, re_addr, re_en, previous_data, previous_valid, reset in itertools.product(
                range(4), range(2), range(2), range(4), range(2), range(2), range(2), range(2)):
            dut = m.FourWordMemory(1)
            dut.words = list(contents)
            dut.read_data, dut.valid = previous_data, bool(previous_valid)
            old = tuple(contents)
            expected_words = list(old)
            expected_data = old[re_addr] if re_en else previous_data
            expected_valid = bool(re_en)
            if wr_en: expected_words[wr_addr] = wr_data
            if reset:
                expected_words, expected_data, expected_valid = [0]*4, 0, False
            assert dut.step(wr_addr, wr_data, bool(wr_en), re_addr, bool(re_en), bool(reset)) == (expected_data, expected_valid)
            assert dut.words == expected_words
            memory_checks += 1
    dut = m.FourWordMemory(64)
    assert dut.step(1, (1 << 64)-1, True, 1, True) == (0, True)
    assert dut.step(re_addr=1, re_en=True) == ((1 << 64)-1, True)
    assert dut.step() == ((1 << 64)-1, False)
    counts['PREP-220'] = {'exhaustive_width1_preedge_transitions': memory_checks,
                         'all_16_contents_all_enables_addresses_output_states_reset': True,
                         'width64_collision_hold_trace': True}

    left_checks = 0
    for n in range(15):
        for bits in itertools.product(range(2), repeat=n):
            dut = m.LeftModulo3()
            assert dut.step(0, valid=False) is False
            number = right_number = 0
            for k, bit in enumerate(bits, 1):
                number += bit << (k-1)
                right_number = 2 * right_number + bit
                hit = dut.step(bit)
                assert dut.state == (number * pow(pow(2, k, 3), -1, 3)) % 3
                assert hit == (number % 3 == 0)
                assert hit == (right_number % 3 == 0)
                before = (dut.state, dut.seen)
                dut.step(1-bit, valid=False)
                assert (dut.state, dut.seen) == before
                left_checks += 1
            assert dut.step(0, reset=True) is False
    counts['PREP-036'] = {'binary_streams_lengths_0_through_14': 32767,
                         'numeric_left_invariant_and_direction_prefix_checks': left_checks,
                         'append_right_same_divisibility_every_checked_prefix': True}
    if write:
        for qid, detail in counts.items():
            result = {'question_id': qid, 'status': 'passed', 'method': 'Python finite transition model against independent oracle',
                      'hdl_compiled': False, 'physical_hardware_tested': False, 'coverage': detail}
            path = BASE / 'checks' / f'{qid.lower()}-batch20-verification.json'
            if path.exists():
                old = json.loads(path.read_text(encoding='utf-8'))
                record = old.get('rtl_verification')
                if record:
                    tb_hash = hashlib.sha256((BASE / record['self_contained_testbench']).read_bytes()).hexdigest()
                    rtl_hash = hashlib.sha256((BASE / record['rtl_source']).read_bytes()).hexdigest()
                    if tb_hash == record['testbench_sha256'] and rtl_hash == record['rtl_source_sha256']:
                        result.update(hdl_compiled=True, hdl_simulated=True, hdl_self_checks_passed=True, rtl_verification=record)
            path.write_text(
                json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return counts


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
