"""Verify the exercise models and optionally compile/run the RTL with Icarus.

Set IVERILOG and VVP to the applicable executable paths if they are not on PATH.
The JSON is written only after all checks, including Icarus, pass.
"""
import argparse
from itertools import product
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'solutions'))
from digital1118_models import (
    count_7e_step,
    dissent,
    expected_test_masks,
    first_array_mismatch,
    nand_library,
    p_n_invert,
    p_n_nor,
    slacks_ps,
    square_check,
)


def square_checks():
    count = 0
    for a, b, c in product(range(16), repeat=3):
        observed = square_check(a, b, c)
        expected = max(a, b, c), a*a + b*b == c*c
        assert observed == expected, (a, b, c, observed, expected)
        count += 1
    for a, b, c in ((255, 255, 255), (0, 255, 255), (128, 0, 127), (153, 204, 255)):
        assert square_check(a,b,c) == (max(a,b,c), a*a+b*b == c*c)
        count += 1
    return count


def combinational_checks():
    for a,b in product(range(2), repeat=2):
        assert p_n_invert(a) == (1,0)[a]
        assert p_n_nor(a,b) == (1,0,0,0)[a*2+b]
        expected = dict(zip(('BUF','NOT','AND','OR','NOR','XOR'), (
            (0,1)[a], (1,0)[a], (0,0,0,1)[a*2+b], (0,1,1,1)[a*2+b],
            (1,0,0,0)[a*2+b], (0,1,1,0)[a*2+b])))
        assert nand_library(a,b) == expected
    for values in product(range(2), repeat=3):
        flag, positions = dissent(*values)
        expected_odd = tuple(int(values.count(v) == 1) for v in values)
        assert (flag, positions) == (len(set(values)) > 1, expected_odd)
        for reference in (0,1):
            expected_errors = tuple(v != reference for v in values)
            if expected_errors.count(True) <= 1:
                assert positions == expected_errors
            if expected_errors.count(True) == 2:
                assert positions == tuple(not wrong for wrong in expected_errors)
            if expected_errors.count(True) == 3:
                assert not flag and not any(positions)
    return 4, 8, 16


def count_checks():
    rng = random.Random(1118)
    tested = 0
    for width in (1,2,4,8):
        maximum = (1 << width) - 1
        history = []
        count, overflow = 0, False
        vectors = [(False, True, i) for i in range(256)]
        vectors.extend((False, True, 0x7E) for _ in range(maximum+3))
        vectors.extend((rng.randrange(16)==0, rng.randrange(2)==1, rng.choice((0x7e,0x7d,rng.randrange(256))))
                       for _ in range(256))
        for reset, valid, data in vectors:
            if reset:
                history.clear()
            elif valid:
                history.append(data)
            matches = history.count(0x7e)
            count, overflow = count_7e_step(count, overflow, data, valid, reset, width)
            assert (count, overflow) == (min(matches, maximum), matches > maximum)
            tested += 1
    return tested


def timing_checks():
    for path in ((300,1800,-150,250), (10,500,1150,-40)):
        d_min, d_max, s, h = path
        assert slacks_ps(2000,100,200,d_min,d_max,150,150) == (s,h)
        assert slacks_ps(2150,100,200,d_min,d_max,150,150) == (s+150,h)
    assert slacks_ps(2000,100,200,50,540,150,150) == (1110,0)
    return 5


def fault_checks():
    masks = expected_test_masks()
    assert len(masks) == 10 and max(mask.bit_count() for mask in masks) == 7
    exact_masks = masks[:-1] + (masks[-1] | 0x3f,)
    assert all(mask.bit_count() == 7 for mask in exact_masks)
    for collection in (masks, exact_masks):
        for bit in range(64):
            assert {word >> bit & 1 for word in collection} == {0,1}
    actual_budget_masks = expected_test_masks(cap=6)
    assert len(actual_budget_masks) == 11
    for bit in range(64):
        assert all((word | (1 << bit)).bit_count() <= 7 for word in actual_budget_masks)

    stored = 0
    writes = []

    def verify(stuck_low, stuck_high):
        writes.clear()
        def write(word):
            nonlocal stored
            assert word.bit_count() <= 7
            writes.append(word)
            stored = (word | stuck_high) & ~stuck_low

        def read():
            return stored

        result = first_array_mismatch(write, read)
        for idx, word in enumerate(masks):
            # Independent bit-by-bit expected readout, including healthy cells.
            expected_read = sum(
                1 << bit for bit in range(64)
                if ((stuck_high >> bit) & 1) or (((word >> bit) & 1) and not ((stuck_low >> bit) & 1))
            )
            if expected_read != word:
                assert result == (idx+1, word, expected_read)
                assert len(writes) == idx+1
                return
        assert result is None and not (stuck_low or stuck_high)
        assert len(writes) == 10

    verify(0,0)
    for bit in range(64):
        verify(1 << bit, 0)
        verify(0, 1 << bit)
    rng = random.Random(370)
    for _ in range(256):
        a,b = rng.getrandbits(64), rng.getrandbits(64)
        verify(a,b & ~a)
    return 129,256


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_native():
    tool = os.environ.get('IVERILOG', 'iverilog')
    runtime = os.environ.get('VVP', 'vvp')
    bench = ROOT / 'checks/digital1118_tb.sv'
    source = ROOT / 'solutions/digital1118.sv'
    with tempfile.TemporaryDirectory() as temporary_directory:
        compiled = Path(temporary_directory) / 'digital1118.vvp'
        subprocess.run([tool,'-g2012','-s','digital1118_tb','-o',str(compiled),str(source),str(bench)],
                       check=True, capture_output=True, text=True)
        output = subprocess.check_output([runtime,str(compiled)], text=True)
        line = next(value for value in output.splitlines() if value.startswith('PASS '))
        result = {name:int(value) for name,value in re.findall(r'(\w+)=(\d+)',line)}
        assert result['square_cases'] == 4096
        assert result['count_samples'] == 526
        assert result['logic_vectors'] == 8
        result['compiler'] = subprocess.check_output([tool,'-V'], text=True, stderr=subprocess.DEVNULL).splitlines()[0]
        result['rtl_sha256'] = digest(source)
        result['testbench_sha256'] = digest(bench)
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json',type=Path,default=ROOT/'checks/digital1118-verification.json')
    args = parser.parse_args()
    gates, votes, diagnosed = combinational_checks()
    single, combinations = fault_checks()
    result = dict(
        status='passed',
        python_model=dict(square_triples=square_checks(), binary_gate_vectors=gates,
                          voter_vectors=votes, voter_diagnoses=diagnosed, counter_samples=count_checks(),
                          timing_examples=timing_checks(), healthy_and_single_fault_memories=single,
                          sample_multiple_fault_memories=combinations),
        rtl=run_native(),
        verification_scope=['Boolean steady-state drive resolution and sampled RTL only.',
                            'Timing examples use arithmetic timing budgets, not timing closure.',
                            'Memory testing uses a deterministic stuck-at model and correct readout, not physical power instrumentation.'],
        sha256={relative:digest(ROOT/relative) for relative in (
            'solutions/digital1118_models.py','checks/check_digital1118.py')},
    )
    data = json.dumps(result, indent=2) + '\n'
    args.json.write_text(data, encoding='utf-8', newline='\n')
    print(data, end='')


if __name__ == '__main__':
    main()
