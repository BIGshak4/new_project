"""Independent oracles for six hardware records; does not claim native HDL."""
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'solutions'))
import prep_hardware_batch1103 as m


def check254():
    checks = 0
    for x in range(8):
        expected = 7 if x == 5 else 5 if x == 7 else x
        assert m.swap57(x) == expected
        assert m.swap57(m.swap57(x)) == x
        checks += 2
    return {'id': 'PREP-254', 'checks': checks, 'scope': 'all eight inputs and involution'}


def check001():
    checks = 0
    for x in range(8):
        out, unused = m.ha3(x)
        assert out == bin(x).count('1') and unused == 0
        checks += 1
    return {'id': 'PREP-001', 'checks': checks, 'scope': 'all eight HA-only inputs and discarded carry'}


def check140():
    checks = 0
    for width in range(1, 13):
        square, odd = 0, 1
        for index in range(1, 4097):
            square, odd = m.square_step(square, odd, width)
            modulus = 2 ** width
            assert square == index ** 2 % modulus
            assert odd == (2 * index + 1) % modulus
            checks += 2
        assert m.square_step(square, odd, width, True) == (0, 1)
        checks += 1
    return {'id': 'PREP-140', 'checks': checks, 'scope': 'widths1..12; 4096 steps each; reset; modulo interpretation'}


def check152():
    checks = 0
    for state in range(32):
        for data in range(32):
            for load in (0, 1):
                low, high = m.extended_step(state & 15, state >> 4, load, data)
                assert (high * 16 + low) == (data if load else (state + 1) % 32)
                checks += 1
    return {'id': 'PREP-152', 'checks': checks, 'scope': '32 states x32 load words x2 control values'}


def check255():
    checks = 0
    for samples in itertools.product((0, 1), repeat=12):
        count = run = 0
        for vin in samples:
            # Output precedes the falling-edge state update. An uninterrupted
            # high run emits at its third high phase only.
            run = run + 1 if vin else 0
            assert m.phase_output(count, vin, 1) == int(run == 3)
            assert m.phase_output(count, vin, 0) == 0
            count = m.phase_step(count, vin)
            assert count == min(run, 3)
            checks += 3
        assert m.phase_step(count, 1, True) == 0
        assert m.phase_output(count, 1, 1, True) == 0
        checks += 2
    return {'id': 'PREP-255', 'checks': checks, 'scope': 'all4096 length12 Vin histories under falling-edge timing contract'}


def check256():
    checks = 0
    for capacity in range(1, 17):
        width = (capacity).bit_length() + 1
        for men in range(capacity + 1):
            for women in range(capacity + 1 - men):
                for event in range(16):
                    new_men, new_women = men, women
                    if event == 8:
                        if not men: continue
                        new_men -= 1
                    elif event == 4:
                        if men + women == capacity: continue
                        new_men += 1
                    elif event == 2:
                        if not women: continue
                        new_women -= 1
                    elif event == 1:
                        if men + women == capacity: continue
                        new_women += 1
                    expected = new_men - new_women
                    actual = m.room_step(men - women, event)
                    assert actual == expected and -(2 ** (width - 1)) <= actual < 2 ** (width - 1)
                    assert m.room_lights(actual) == (int(new_men > new_women), int(new_men == new_women), int(new_men < new_women))
                    checks += 2
    return {'id': 'PREP-256', 'checks': checks, 'scope': 'capacities1..16, all legal populations/events; invalid words hold'}


CHECKS = {1: check001, 140: check140, 152: check152, 254: check254, 255: check255, 256: check256}
if __name__ == '__main__':
    result = {'status': 'passed', 'kind': 'independent_python_models', 'records': [f() for f in CHECKS.values()],
              'limitations': 'Finite software checks, not HDL compilation or physical timing signoff.'}
    result['checks'] = sum(row['checks'] for row in result['records'])
    Path(__file__).with_name('batch1103-hardware-python-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result))
