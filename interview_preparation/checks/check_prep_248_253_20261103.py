"""Independent bounded checks for six November 3 concept/reasoning questions.

No device, network, live service or C++ compiler is invoked by this script.
The separate C++ harness is an actual native-compiler input, not emulated here.
"""
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random

BANK = Path(__file__).resolve().parents[1]


def module(number, filename):
    spec = importlib.util.spec_from_file_location(f'prep{number}', BANK/'solutions'/filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    height = module(248, 'prep_248_ideal_height.py')
    db = module(249, 'prep_249_decibel_ratios.py')
    hats = module(250, 'prep_250_online_hat_partition.py')
    weights = module(251, 'prep_251_additive_weights.py')
    spike = module(253, 'prep_253_spike_capacity_model.py')
    counts = {}
    checks = 0
    for gravity in (1.62, 3.71, 9.81, 24.79):
        for n in range(301):
            time = n/10
            # Independent integration of velocity over 200 small intervals.
            step = time/200
            integrated = math.fsum(gravity*(i+0.5)*step*step for i in range(200))
            assert math.isclose(height.height_from_fall_time(time, gravity), integrated,
                                rel_tol=1e-12, abs_tol=1e-12)
            low, high = height.height_interval(time, 0.05, gravity)
            assert low <= integrated + 1e-10 <= high + 1e-10
            checks += 1
    assert math.isclose(height.height_from_fall_time(2), 19.62)
    counts[248] = checks
    checks = 0
    with localcontext() as ctx:
        ctx.prec = 50
        for a in range(1, 31):
            for b in range(1, 31):
                oracle = float(Decimal(10)*(Decimal(a)/Decimal(b)).ln()/Decimal(10).ln())
                assert math.isclose(db.power_db(a,b), oracle, abs_tol=1e-12)
                # Physical power computation, independently of voltage-db code.
                assert math.isclose(db.voltage_db_equal_impedance(a,b),
                                    db.power_db(a*a/50,b*b/50), abs_tol=1e-12)
                assert math.isclose(db.power_db(a,b)+db.power_db(b,a), 0, abs_tol=1e-12)
                checks += 1
    assert math.isclose(db.watts_to_dbm(0.001), 0, abs_tol=1e-12)
    assert math.isclose(db.watts_to_dbm(1), 30, abs_tol=1e-12)
    counts[249] = checks + 2
    checks = 0
    for length in range(13):
        for colors in itertools.product((0,1), repeat=length):
            result = hats.simulate_arrival(colors)
            assert [c for _,c in result] == sorted(colors)
            assert sorted(i for i,_ in result) == list(range(length))
            prior = []
            for ident, color in enumerate(colors):
                gap = hats.choose_gap([c for _,c in prior])
                for possible in (0,1):
                    candidate = prior[:gap]+[(ident,possible)]+prior[gap:]
                    assert [c for _,c in candidate] == sorted(c for _,c in candidate)
                    assert [i for i,_ in candidate if i != ident] == [i for i,_ in prior]
                prior.insert(gap,(ident,color))
            checks += 1
    rng = random.Random(1103)
    for _ in range(200):
        colors = [0]*25+[1]*25
        rng.shuffle(colors)
        assert [c for _,c in hats.simulate_arrival(colors)] == [0]*25+[1]*25
        checks += 1
    counts[250] = checks
    checks = 0
    for maximum in range(256):
        offered = weights.binary_weights(maximum)
        reachable = {sum(v for index,v in enumerate(offered) if mask>>index&1)
                     for mask in range(1<<len(offered))}
        assert set(range(maximum+1)) <= reachable
        if maximum:
            assert 2**(len(offered)-1) < maximum+1 <= 2**len(offered)
        for target in range(maximum+1):
            chosen = weights.select_weights(target, offered)
            assert sum(chosen) == target and len(set(chosen)) == len(chosen)
            assert set(chosen) <= set(offered)
            checks += 1
    assert len(weights.binary_weights(40)) == 6
    assert set(weights.select_weights(17, weights.binary_weights(40))) == {1,16}
    counts[251] = checks
    checks = 0
    for capacity in range(1,5):
        for limit in range(5):
            for arrivals in itertools.product(range(6), repeat=4):
                actual = spike.simulate_slots(arrivals, capacity, limit)
                depth = 0
                for count, row in zip(arrivals, actual):
                    # Algebraic fluid-slot recurrence; no queue/batch mechanism.
                    discarded = max(0, depth+count-capacity-limit)
                    served = min(capacity, depth+count)
                    depth = max(0, depth+count-capacity-discarded)
                    assert row['rejected'] == discarded
                    assert row['completed'] == served
                    assert row['backlog'] == depth <= limit
                    assert row['admitted']+row['rejected'] == count
                assert sum(arrivals) == sum(r['completed']+r['rejected'] for r in actual)+depth
                checks += 1
    for peak in range(100):
        for capacity in range(3,8):
            for util in (Fraction(1,2),Fraction(3,4),Fraction(1)):
                reserve = 1
                independent = next(n for n in range(reserve,500)
                                   if (n-reserve)*capacity*util >= peak)
                assert spike.required_instances(peak,capacity,util,reserve) == independent
                checks += 1
    counts[253] = checks
    invalid = 0
    for function, args in [
        (height.height_from_fall_time,(-1,)), (height.height_from_fall_time,(math.inf,)),
        (height.height_from_fall_time,(1,0)), (height.height_interval,(1,-1)),
        (db.power_db,(0,1)), (db.power_db,(1,-1)), (db.voltage_db_equal_impedance,(math.nan,1)),
        (weights.binary_weights,(-1,)), (weights.binary_weights,(1.5,)),
        (weights.select_weights,(-1,[1])), (weights.select_weights,(9,[1,2,4])),
        (hats.choose_gap,([2],)), (spike.simulate_slots,([1],0,2)),
        (spike.simulate_slots,([1,-1],2,2)), (spike.required_instances,(1,0)),
    ]:
        try:
            function(*args)
        except ValueError:
            invalid += 1
        else:
            raise AssertionError((function.__name__,args))
    descriptions = {
        248: '1,204 ideal-height cases versus midpoint velocity integration; exact timing bounds. No physical measurement.',
        249: '900 positive-power ratio pairs versus 50-digit Decimal logarithms and independently squared RMS voltages; two dBm anchors.',
        250: 'All 8,191 arrival strings of length 0..12, both possible newcomer colors at every insertion and stationary prior order; 200 source-sized 25/25 permutations.',
        251: 'All target values for maxima 0..255 versus enumerated subset sums; six-weight source example and information-count bound.',
        252: 'C++ semantics reviewed against primary draft and Core Guidelines. A separate GCC C++17 invocation with -O2 -Wall -Wextra -Werror -pedantic compiled and ran the supplied 65-size ownership harness successfully, with empty stderr. This Python invocation does not compile C++.',
        253: '25,920 bounded queue traces versus algebraic recurrence and conservation; 1,500 capacity calculations versus independent minimal-instance enumeration. This is a discrete illustrative model, not production load testing.',
    }
    for number, description in descriptions.items():
        result = dict(question_id=f'PREP-{number}', status='passed',
                      received_on='2026-11-03', method='Python independent models' if number != 252 else 'Primary-reference review plus separately recorded GCC C++17 native run',
                      cases=counts.get(number,65 if number == 252 else 0), verification=description,
                      limitations='Finite model coverage does not certify physical measurement, production capacity or professional human review.')
        if number == 252:
            result['native_evidence_path'] = 'checks/batch1103-native-verification.json'
            result['native_source_sha256'] = hashlib.sha256((BANK/'solutions/prep_252_copy_constructor.cpp').read_bytes()).hexdigest()
            result['native_harness_sha256'] = hashlib.sha256((BANK/'checks/check_prep_252_copy_constructor_native.cpp').read_bytes()).hexdigest()
            result['native_compile_performed_by_this_python_script'] = False
        (BANK/f'checks/prep-{number}-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    summary = dict(status='passed', cases_by_question=counts, rejected_invalid_cases=invalid,
                   total_model_cases=sum(counts.values()), cpp_compiled_by_this_python_script=False,
                   separate_cpp_native_evidence='checks/batch1103-native-verification.json')
    (BANK/'checks/batch1103-concepts-verification.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
