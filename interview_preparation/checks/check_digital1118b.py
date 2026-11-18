"""Run model checks, exhaustive small-width register tests and Icarus gate simulation."""

import hashlib
import json
import math
import subprocess
import sys
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / 'solutions'))
from digital1118b_models import copy_instructions, follower, open_loop


def simulate(program, width, a, b, flag_machine=False):
    registers = [a, b]
    pc = 0
    maximum = (1 << width) - 1
    zero = None
    while pc < len(program):
        op, r, *extra = program[pc]
        pc += 1
        if op == 'JMPZ':
            if (zero if flag_machine else registers[r] == 0):
                pc = extra[0]
        else:
            value = registers[r] + {'INC': 1, 'DEC': -1}[op]
            if not flag_machine:
                assert 0 <= value <= maximum
            registers[r] = value & maximum
            zero = registers[r] == 0
    return registers


def using_flag_tests(program):
    """Expand each JMPZ R,L into INC R, DEC R, JMPZ L and relocate labels."""
    address = [0]
    for op, *_ in program:
        address.append(address[-1] + (3 if op == 'JMPZ' else 1))
    result = []
    for op, r, *args in program:
        if op == 'JMPZ':
            result.extend([('INC', r), ('DEC', r), ('JMPZ', r, address[args[0]])])
        else:
            result.append((op, r))
    return result


def main():
    count = 0
    for width in range(1, 6):
        program = copy_instructions(width)
        flag_program = using_flag_tests(program)
        for a, b in product(range(1 << width), repeat=2):
            assert simulate(program, width, a, b) == [a, a]
            assert simulate(flag_program, width, a, b, flag_machine=True) == [a, a]
            count += 1

    dc_cases = 0
    for gain in (1, 10, 1000, 100_000):
        for vin in (-8, -4, -1, 0, 1, 4, 8):
            output = follower(vin, gain, -4, 4)
            assert math.isclose(output, open_loop(vin, output, gain, -4, 4), abs_tol=1e-9)
            dc_cases += 1
    assert open_loop(0.001, 0, 100_000, -4, 4) == 4
    assert math.isclose(follower(1, 100_000, -4, 4), 0.999990, abs_tol=1e-9)
    assert follower(5, 100_000, -4, 4) == 4

    rtl = BANK / 'solutions/digital1118b.sv'
    bench = BANK / 'checks/digital1118b_tb.sv'
    with TemporaryDirectory() as folder:
        binary = Path(folder) / 'gates.vvp'
        subprocess.run(['iverilog', '-g2012', '-s', 'digital1118b_tb', '-o', binary, rtl, bench], check=True)
        run = subprocess.run(['vvp', binary], capture_output=True, text=True, check=True)
        assert 'PASS: AOI21, XOR, four-channel selector' in run.stdout
    files = (rtl, bench, BANK / 'solutions/digital1118b_models.py', Path(__file__).resolve())
    evidence = {
        'status': 'passed',
        'checked': {'follower_dc_cases': dc_cases, 'register_pairs_per_instruction_model': count,
                    'register_widths': '1..5 inclusive', 'instruction_models': ['register-tested branch', 'zero-flag branch'],
                    'aoi21_switch_vectors': 8, 'xor_distinct_vectors': 4, 'mux_tree_vectors': 64},
        'scope': 'Educational DC and settled-state Icarus models. Register examples are exact integer simulations.',
        'sha256': {p.relative_to(BANK).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    }
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
