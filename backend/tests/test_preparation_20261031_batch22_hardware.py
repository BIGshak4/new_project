"""Independent equation, byte, state and driver oracles for the new intake.

Local cases execute Python teaching models, not SPICE or HDL. Separate strict
C99 compilation/runtime evidence is bound to the exact C sources and harness.
"""
from __future__ import annotations

import importlib.util
import itertools
import math
import random
from functools import reduce
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOL = ROOT / 'interview_preparation/solutions'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SOL / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LPF = load('prep_221_lpf')
INT = load('prep_222_integrator')
RAM = load('prep_223_ramp_memory')
COPY = load('prep_227_register_copy')
NAND = load('prep_015_nand_batch22')
POP = load('prep_151_uint32_popcount_batch22')


def rk4(function, initial, time, steps=600):
    if not time:
        return initial
    h, value = time / steps, initial
    for i in range(steps):
        t = i * h
        k1 = function(t, value)
        k2 = function(t + h/2, value + h*k1/2)
        k3 = function(t + h/2, value + h*k2/2)
        k4 = function(t + h, value + h*k3)
        value += h * (k1 + 2*k2 + 2*k3 + k4) / 6
    return value


@pytest.mark.parametrize('r,c', [(1000,1e-9),(10000,1e-8),(330,1e-6)])
@pytest.mark.parametrize('ratio', [0,0.1,1,10,100])
def test_lpf_frequency_from_independent_node_admittance(r, c, ratio):
    frequency = ratio / (2*math.pi*r*c)
    yr, yc = 1/r, 2j*math.pi*frequency*c
    result = LPF.response(r,c,frequency)
    assert result == pytest.approx(yr / (yr + yc))
    assert (1-result)/r == pytest.approx(yc*result)


@pytest.mark.parametrize('vin,initial', [(1,0),(0,2),(-1,1)])
@pytest.mark.parametrize('multiples', [0,0.1,1,3,8])
def test_lpf_step_matches_independent_ode(vin, initial, multiples):
    r,c = 1000,1e-6
    time = multiples*r*c
    reference = rk4(lambda t,v: (vin-v)/(r*c), initial, time)
    assert LPF.step(r,c,vin,initial,time) == pytest.approx(reference,abs=1e-9)


def test_lpf_cutoff_loading_and_follower_equation():
    r,c = 10000,10e-9
    fc = LPF.cutoff(r,c)
    assert fc == pytest.approx(1591.5494309189535)
    magnitude,phase = LPF.magnitude_phase(r,c,fc)
    assert magnitude == pytest.approx(math.sqrt(0.5))
    assert phase == pytest.approx(-math.pi/4)
    for gain in [1,10,10000]:
        out = LPF.follower(2,gain)
        assert out == pytest.approx(gain*(2-out))
        assert out < 2
    # Loading cannot be silently omitted: at DC R and RL divide voltage.
    assert 10000/(r+10000) == 0.5 != abs(LPF.response(r,c,0))


@pytest.mark.parametrize('vin,initial,time', list(itertools.product([-0.2,0,0.1],[0,0.3],[0,0.001,0.004])))
def test_integrator_constant_ode_and_initial_condition(vin, initial, time):
    r,c = 10000,100e-9
    reference = rk4(lambda t,v: -vin/(r*c), initial, time)
    assert INT.constant_input(r,c,vin,initial,time) == pytest.approx(reference,abs=1e-11)


@pytest.mark.parametrize('omega,time', [(10,0.1),(100,0.02),(1000,0.001),(500,0)])
def test_integrator_sinusoid_numerical_area(omega,time):
    r,c,amp,initial = 1000,1e-6,0.1,0.3
    ref = rk4(lambda t,v: -amp*math.sin(omega*t)/(r*c),initial,time)
    assert INT.sinusoid(r,c,amp,omega,initial,time) == pytest.approx(ref,abs=1e-10)
    assert INT.sinusoid(r,c,amp,omega,initial,0) == initial


def test_integrator_piecewise_rails_and_parallel_resistor():
    segments = [(0.001,0.1),(0.002,-0.2),(0.003,0.0)]
    area = sum(duration*voltage for duration,voltage in segments)
    assert INT.piecewise_constant(10000,100e-9,0.2,segments) == pytest.approx(0.2-area/0.001)
    assert INT.dc_rail_time(10000,100e-9,0.1,0,-5,5) == pytest.approx(0.05)
    assert INT.dc_rail_time(10000,100e-9,-0.1,0,-5,5) == pytest.approx(0.05)
    assert math.isinf(INT.dc_rail_time(1,1,0,0,-1,1))
    for rf in [10000,100000]:
        for frequency in [0,100,1000]:
            feedback_admittance = 1/rf + 2j*math.pi*frequency*100e-9
            assert INT.practical_response(10000,100e-9,rf,frequency) == pytest.approx(-1/(10000*feedback_admittance))


@pytest.mark.parametrize('endian,signed', list(itertools.product(['little','big'],[False,True])))
def test_ramp_complete_byte_coverage_and_all_start_boundaries(endian,signed):
    memory = bytes(range(256))
    for all_offsets,expected_count in [(False,64),(True,253)]:
        addresses=[]
        def read(address, all_offsets=all_offsets, addresses=addresses):
            assert 0 <= address <= 252
            if not all_offsets:
                assert address % 4 == 0
            addresses.append(address)
            return int.from_bytes(memory[address:address+4],endian,signed=signed)
        assert RAM.validate(read,endian,all_offsets) == (True,expected_count)
        assert len(addresses) == expected_count
        assert set().union(*(set(range(a,a+4)) for a in addresses)) == set(range(256))
        assert addresses[-1] == 252
    for address in range(253):
        assert RAM.expected_word(address,endian) == int.from_bytes(memory[address:address+4],endian)


@pytest.mark.parametrize('endian',['little','big'])
def test_every_single_bit_corruption_of_the_ramp_is_detected(endian):
    memory = bytearray(range(256))
    for address, bit in itertools.product(range(256),range(8)):
        memory[address] ^= 1 << bit
        ok,count = RAM.validate(lambda a:int.from_bytes(memory[a:a+4],endian),endian)
        assert not ok and 1 <= count <= 64
        memory[address] ^= 1 << bit
    assert RAM.expected_word(0,'little') == 0x03020100
    assert RAM.expected_word(0,'big') == 0x00010203


@pytest.mark.parametrize('width',range(1,7))
def test_all_parallel_and_serial_register_word_pairs(width):
    for a,b in itertools.product(range(1 << width),repeat=2):
        assert COPY.parallel(a,b,width) == (a,a)
        final_a,final_b,trace = COPY.serial(a,b,width)
        assert (final_a,final_b) == (a,a) and len(trace) == width+1
        # Independent little-endian bit-list shifting, not integer shifts.
        aa=[int(v) for v in f'{a:0{width}b}'[::-1]]
        bb=[int(v) for v in f'{b:0{width}b}'[::-1]]
        for state in trace[1:]:
            outgoing=aa[0]
            aa=aa[1:]+[outgoing]
            bb=bb[1:]+[outgoing]
            assert state == (int(''.join(map(str,aa[::-1])),2),int(''.join(map(str,bb[::-1])),2))


def test_register_larger_samples_and_nand_defined_nets():
    rng=random.Random(20261031)
    for width in [8,16,32,64]:
        for _ in range(30):
            a,b=rng.getrandbits(width),rng.getrandbits(width)
            assert COPY.serial(a,b,width)[:2] == (a,a)
    for x,y in itertools.product([0,1],repeat=2):
        active=[v for v in NAND.drivers(x,y) if v!='Z']
        assert active and len(set(active))==1
        assert NAND.nand(x,y)==int(x*y==0)
    assert NAND.drivers(0,0)==[1,1,'Z']
    assert NAND.minimum_direct_cover(False)==NAND.minimum_direct_cover(True)==3
    # Independent direct-cover impossibility at costs one and two, using
    # driver masks instead of executing the author cell functions.
    signals=[0b1100,0b1010,0,15]
    high={15^(a|b) for a,b in itertools.product(signals,repeat=2)}
    low={a&b for a,b in itertools.product(signals,repeat=2)}
    drivers=[(mask,0) for mask in high]+[(0,mask) for mask in low]
    for k in [1,2]:
        for choice in itertools.combinations_with_replacement(drivers,k):
            up=reduce(int.__or__, (high_mask for high_mask,low_mask in choice),0)
            down=reduce(int.__or__, (low_mask for high_mask,low_mask in choice),0)
            assert not (up==7 and down==8)


def test_uint32_popcount_exhaustive_low_domain_and_deterministic_words():
    for value in range(1 << 16):
        assert POP.popcount(value)==bin(value).count('1')
    rng=random.Random(15122)
    values=[0,1,0xffffffff,0x80000000,0xaaaaaaaa,0x55555555]
    values.extend(rng.getrandbits(32) for _ in range(1024))
    for value in values:
        assert POP.popcount(value)==sum(int(bit) for bit in f'{value:032b}')
    with pytest.raises(ValueError):
        POP.popcount(-1)
    with pytest.raises(ValueError):
        POP.popcount(1 << 32)


def test_proposed_c_unsigned_shifts_and_explicit_not_compiled_scope():
    ramp=(SOL/'prep_223_ramp_memory.c').read_text(encoding='utf-8')
    pop=(SOL/'prep_151_uint32_popcount_batch22.c').read_text(encoding='utf-8')
    assert '(uint32_t)(a + j) << shift' in ramp and 'a <= 252u' in ramp
    assert '(uint32_t)read(a)' in ramp
    assert 'uint32_t x' in pop and 'x &= x - 1u' in pop
    assert 'not compiled' in ramp and 'not compiled' in pop


def test_isolated_native_c99_evidence_is_bound_to_the_exact_sources():
    import hashlib
    import json

    root = SOL.parents[1]
    evidence = json.loads((SOL.parent/'checks/batch22-hardware-native-verification.json').read_bytes())
    assert evidence['passed']
    assert evidence['compile_exit'] == evidence['run_exit'] == 0
    assert evidence['compiler'] == 'gcc' and evidence['network'] == 'deny-all'
    assert evidence['persistent'] is False and evidence['stopped'] is True
    assert {'-std=c99', '-Wall', '-Wextra', '-Werror', '-pedantic'} <= set(evidence['flags'])
    for relative, digest in evidence['canonical_lf_source_sha256'].items():
        assert hashlib.sha256((root/relative).read_text(encoding='utf-8').encode()).hexdigest() == digest
    assert evidence['coverage']['memory_cases'] == 4 * (1 + 256 * 8)
    assert evidence['coverage']['popcount_cases'] == 65536 + 64 + 1 + 20000
