"""Independent numerical/state oracles for the eight batch90 hardware records.

Python logical models are executed; supplied SystemVerilog is not compiled here.
"""
import importlib.util
import random
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def model(name):
    spec = importlib.util.spec_from_file_location(name, BANK / 'solutions' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check179():
    m = model('prep_179_serial_divide_five')
    observations = 0
    for size in range(13):
        for bits in product((0, 1), repeat=size):
            number = 0
            for bit, (q, r, digit) in zip(bits, m.divide_stream(bits), strict=True):
                number = 2 * number + bit
                assert (q, r) == divmod(number, 5)
                assert digit == (q & 1)
                observations += 1
    transitions = [[r, b, *m.step(r, b)] for r in range(5) for b in (0, 1)]
    # Every residue has a different future quotient on the same continuation000.
    futures = []
    for r in range(5):
        digits = []
        for bit in (0, 0, 0):
            r, digit = m.step(r, bit)
            digits.append(digit)
        futures.append(tuple(digits))
    assert len(set(futures)) == 5
    assert m.divide_stream([1] * 256)[-1][:2] == divmod((1 << 256) - 1, 5)
    return {'status':'passed','words':8191,'prefix_observations':observations,
            'transitions':transitions,'five_distinguishable_states':True,
            'constant_one_prefix_bits':256,'hdl_compiled':False}


def check180():
    m = model('prep_180_binary_mean')
    cases = 0
    for width in range(1, 8):
        for a in range(1 << width):
            for b in range(1 << width):
                whole, half = m.mean_unsigned(a, b, width)
                assert 2 * whole + half == a + b
                assert 0 <= whole < (1 << width) and half in (0, 1)
                assert (whole, half) == m.mean_without_wide_sum(a, b, width)
                cases += 1
    assert m.mean_unsigned(255, 255, 8) == (255, 0)
    assert m.mean_unsigned(0, 255, 8) == (127, 1)
    return {'status':'passed','exhaustive_widths':'1..7','pairs':cases,'eight_bit_boundary_cases':2,'hdl_compiled':False}


def check181():
    m = model('prep_181_bcd_times_three')
    rows = []
    for word in range(16):
        valid, tens, ones = m.bcd_times_three(word)
        assert valid == int(word <= 9)
        if valid:
            assert 10 * tens + ones == 3 * word and 0 <= tens <= 2 and 0 <= ones < 10
        else:
            assert (tens, ones) == (0, 0)
        rows.append([word, valid, tens, ones])
    return {'status':'passed','exhaustive_input_words':16,'rows':rows,'hdl_compiled':False}


def check016():
    m = model('prep_016_lsb_priority_batch90')
    cases = 0
    for word in range(65536):
        positions = [i for i in range(16) if word & (1 << i)]
        expected = (1, positions[0]) if positions else (0, 0)
        for inactive in ((0,0,0,0),(3,2,1,0),(3,3,3,3),(1,3,2,3)):
            assert m.pe16_low(word, inactive, 3) == expected
            cases += 1
    for word in range(256):
        indices = [i for i in range(8) if (word >> i) & 1]
        assert m.pe8_gates_low(word) == ((1, indices[0]) if indices else (0,0))
    assert m.pe16_low(1) == (1,0) and m.pe16_low(0) == (0,0)
    return {'status':'passed','hierarchy_cases':cases,'eight_input_gate_cases':256,
            'inactive_local_codes_varied':True,'priority':'lowest input index','hdl_compiled':False}


def check122():
    m = model('prep_122_half_full_adder_batch90')
    rows = []
    for a,b in product((0,1),repeat=2):
        s,c = m.half_adder(a,b)
        assert s + 2*c == a+b
    for a,b,cin in product((0,1),repeat=3):
        s,c = m.full_adder(a,b,cin)
        assert s + 2*c == a+b+cin
        g,h = a*b, (a ^ b)*cin
        assert g*h == 0 and (g ^ h) == (g | h)
        rows.append([a,b,cin,s,c])
    return {'status':'passed','half_adder_cases':4,'full_adder_cases':8,'rows':rows,
            'mutually_exclusive_carries':True,'external_or_gate':False,'hdl_compiled':False}


def check095():
    m = model('prep_095_six_of_seven_batch90')
    observations = 0
    for size in range(13):
        for bits in product((0,1),repeat=size):
            for i,(alarm,count,filled,history) in enumerate(m.monitor(bits)):
                recent=bits[max(0,i-6):i+1]
                assert count == sum(recent) and filled == min(7,i+1)
                assert alarm == int(i>=6 and sum(recent)>=6)
                assert history == sum(bit << j for j,bit in enumerate(reversed(recent)))
                observations += 1
    assert [x[0] for x in m.monitor([1]*8)] == [0]*6+[1,1]
    assert m.monitor([1]*6+[0])[-1][0] == 1
    return {'status':'passed','words':8191,'prefix_observations':observations,
            'warmup_policy':'full seven-sample windows only','hdl_compiled':False}


def check078():
    m = model('prep_078_fiftieth_edge_batch90')
    trace = m.clock_pulses(10000)
    assert [i+1 for i,(pulse,_) in enumerate(trace) if pulse] == list(range(50,10001,50))
    rng=random.Random(781790)
    transitions=0
    for _ in range(100):
        bits=[rng.randrange(2) for _ in range(2000)]
        rises=previous=0
        for bit,pulse in zip(bits,m.input_event_pulses(bits),strict=True):
            rising=bool(bit and not previous)
            rises+=rising
            assert pulse == int(rising and rises % 50 == 0)
            previous=bit
            transitions+=1
    square=m.divided_square(10000)
    assert square[24]==1 and square[49]==0
    for start in range(0,10000,50):
        assert sum(square[start:start+50])==25
    return {'status':'passed','clock_edges':10000,'sampled_event_observations':transitions,
            'optional_square_cycles':10000,'pulse_duty_cycle':'1/50','square_duty_cycle':'1/2',
            'hdl_compiled':False}


def check076():
    m = model('prep_076_memory_capacity_batch90')
    assert m.interface_tests(m.Memory())
    faults = []
    for bit in range(10):
        assert not m.interface_tests(m.Memory(alias_bit=bit))
        faults.append('address line '+str(bit)+' tied low')
    for bit in range(16):
        assert not m.interface_tests(m.Memory(stuck_zero_bit=bit))
        faults.append('data line '+str(bit)+' stuck0')
    return {'status':'passed','healthy_models':1,'detected_fault_models':len(faults),'faults':faults,
            'capacity_bits':1024*16,'capacity_bytes':2048,
            'scope':'Destructive logical model with deterministic conventional read/write, not physical fault qualification.'}


CHECKS={'179':check179,'180':check180,'181':check181,
        '016_lsb_priority':check016,'122_ha_fa':check122,'095_six_of_seven':check095,
        '078_fiftieth_edge':check078,'076_capacity':check076}
