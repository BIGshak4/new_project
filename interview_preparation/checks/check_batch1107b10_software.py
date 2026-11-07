"""Independent software checks; no actuator, network, database or learner writes."""
import ast
import importlib.util
import itertools
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOL = ROOT / 'solutions'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SOL / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sort_check():
    function = load('prep_273_heapsort_batch1107b10').sort_array
    count = 0
    for length in range(9):
        for values in itertools.product((-1, 0, 1), repeat=length):
            work = list(values)
            identity = id(work)
            assert function(work) is work
            assert id(work) == identity and work == sorted(values)
            count += 1
    rng = random.Random(1107)
    for _ in range(240):
        values = [rng.randint(-1000, 1000) for _ in range(rng.randrange(600))]
        work = values[:]
        assert function(work) == sorted(values)
        count += 1
    for values in ([2**100, -(2**100), 0, 2**100], list(range(1000)),
                   list(range(1000, 0, -1)), [7] * 1000):
        work = values[:]
        assert function(work) == sorted(values)
        count += 1
    tree = ast.parse((SOL / 'prep_273_heapsort_batch1107b10.py').read_text('utf-8'))
    assert not any(isinstance(node, ast.Call) and (
        isinstance(node.func, ast.Name) and node.func.id == 'sorted'
        or isinstance(node.func, ast.Attribute) and node.func.attr == 'sort')
        for node in ast.walk(tree))
    return {'cases': count, 'exhaustive_arrays': 9841,
            'oracle': 'independent built-in sort, list identity and multiplicity preservation',
            'candidate_builtin_sort_absent': True}


def subset_oracle(values, target):
    return any(sum(values[index] for index in range(len(values)) if mask >> index & 1) == target
               for mask in range(1, 1 << len(values)))


def subset_check():
    function = load('prep_040_subset_sum_batch1107b10').has_subset_sum
    count = 0
    for length in range(7):
        for values in itertools.product((-1, 0, 1), repeat=length):
            for target in range(-4, 5):
                work = list(values)
                assert function(work, target) is subset_oracle(values, target)
                assert work == list(values)
                count += 1
    rng = random.Random(401107)
    for _ in range(200):
        values = [rng.randint(-20, 20) for _ in range(rng.randrange(13))]
        target = rng.randint(-50, 50)
        assert function(values, target) is subset_oracle(values, target)
        count += 1
    for values, target, expected in [([], 0, False), ([0], 0, True),
                                     ([3, -3], 0, True), ([2], 4, False),
                                     ([2, 2], 4, True), ([-7], -7, True)]:
        assert function(values, target) is expected
        count += 1
    return {'cases': count, 'oracle': 'enumerate every nonempty physical-index subset',
            'negative_zero_duplicates_and_no_index_reuse': True, 'input_unchanged': True}


def light(ex, ey, scale=10.0):
    return [scale * (1 - ex + ey), scale * (1 + ex + ey),
            scale * (1 - ex - ey), scale * (1 + ex - ey)]


def solar_check():
    module = load('prep_275_solar_tracker_batch1107b10')
    count = 0
    for ix, iy in itertools.product(range(-20, 21), repeat=2):
        ex, ey = ix / 50, iy / 50
        sample = {'stamp': 10.0, 'angles': [0.0, 45.0],
                  'light': light(ex, ey), 'confident': True}
        result = module.TrackingCore().step(sample, 10.1)
        assert result['mode'] == 'TRACK_LOCAL'
        for key, error in [('az_rate', ex), ('el_rate', ey)]:
            value = result[key]
            assert abs(value) <= 2.0
            if abs(error) < .019:
                assert value == 0.0
            elif abs(error) > .021:
                assert value * error > 0.0
        count += 1
    stopped = 0
    base = {'stamp': 1.0, 'angles': [0.0, 45.0], 'light': [10.0] * 4, 'confident': True}
    variants = [dict(base, stamp=-10.0), dict(base, stamp=2.0),
                dict(base, light=[-1, 2, 3, 4]), dict(base, light=[math.nan] * 4),
                dict(base, light=[1e308] * 4), dict(base, angles=[91, 20]),
                dict(base, angles=[0, -1]), dict(base, light=[1, 2, 3]),
                dict(base, confident='yes'), {}]
    for sample in variants:
        controller = module.TrackingCore()
        result = controller.step(sample, 1.0)
        assert result == {'mode': 'FAULT', 'az_rate': 0.0, 'el_rate': 0.0}
        assert controller.step(base, 1.0)['mode'] == 'FAULT'
        controller.reset_after_check()
        assert controller.step(base, 1.0)['mode'] == 'TRACK_LOCAL'
        stopped += 1
    for sample, expected in [(dict(base, light=[0.0] * 4), 'HOLD_DARK'),
                             (dict(base, confident=False), 'HOLD_UNCERTAIN')]:
        result = module.TrackingCore().step(sample, 1.0)
        assert result == {'mode': expected, 'az_rate': 0.0, 'el_rate': 0.0}
        stopped += 1
    for angles, optical, axis in [([-90, 45], (-.2, 0), 'az_rate'),
                                  ([90, 45], (.2, 0), 'az_rate'),
                                  ([0, 0], (0, -.2), 'el_rate'),
                                  ([0, 90], (0, .2), 'el_rate')]:
        sample = dict(base, angles=angles, light=light(*optical))
        assert module.TrackingCore().step(sample, 1.0)[axis] == 0.0
        stopped += 1
    steps = 0
    for target_az, target_el in itertools.product((-8, -4, 0, 4, 8), (37, 41, 45, 49, 53)):
        controller = module.TrackingCore()
        az, el = 0.0, 45.0
        for index in range(80):
            before = abs(target_az - az) + abs(target_el - el)
            now = index / 10
            sample = {'stamp': now, 'angles': [az, el],
                      'light': light((target_az - az) / 20, (target_el - el) / 20),
                      'confident': True}
            result = controller.step(sample, now)
            az += result['az_rate'] * .1
            el += result['el_rate'] * .1
            assert abs(target_az - az) + abs(target_el - el) <= before + 1e-10
            steps += 1
    return {'quadrant_response_cases': count, 'stop_limit_and_fault_cases': stopped,
            'synthetic_local_plant_steps': steps,
            'scope': 'unit checks and a declared linear capture-cone plant only; no ephemeris, drive, encoder or physical rig validation'}


def main():
    results = {273: sort_check(), 40: subset_check(), 275: solar_check()}
    for number, data in results.items():
        path = ROOT / 'checks' / f'prep-{number:03d}-batch1107b10-verification.json'
        path.write_text(json.dumps(dict(status='passed', checked_on='2026-11-07', **data), indent=2) + '\n', encoding='utf-8')
    aggregate = {'status': 'passed', 'checked_on': '2026-11-07', 'questions': results}
    (ROOT / 'checks' / 'batch1107b10-software-verification.json').write_text(json.dumps(aggregate, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(aggregate, indent=2))


if __name__ == '__main__':
    main()
