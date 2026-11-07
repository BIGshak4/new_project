"""Independent bounded arithmetic/search checks; no SPICE or physical claims."""
from __future__ import annotations

import importlib.util
import itertools
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'solutions' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analog = load('prep_258_260_analog_models')
focus = load('prep_270_focus_search')
coins = load('prep_271_single_use_coin_payment')
results = {}


def record(number, count, method, scope, **extra):
    data = dict(status='passed', checked_on='2026-11-07', checks=count,
                method=method, scope=scope, **extra)
    results[str(number)] = data
    (ROOT / 'checks' / f'prep-{number}-verification.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


# The line ODE has normalized y'=2A-y. RK4 is independent of the closed form.
count = 0
for incident, z0, cap in itertools.product((-2.0, 0.0, 0.3, 1.0, 5.0), (25.0, 50.0, 120.0), (1e-12, 5e-11)):
    value = 0.0
    h = 0.01
    for step in range(1001):
        voltage, reflected, current = analog.capacitive_line_step(incident, z0, cap, step * h * z0 * cap)
        assert math.isclose(voltage, value, rel_tol=1e-8, abs_tol=1e-8)
        assert math.isclose(voltage, incident + reflected, abs_tol=1e-14)
        assert math.isclose(current, (incident - reflected) / z0, abs_tol=1e-14)
        k1 = 2 * incident - value
        k2 = 2 * incident - (value + h * k1 / 2)
        k3 = 2 * incident - (value + h * k2 / 2)
        k4 = 2 * incident - (value + h * k3)
        value += h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        count += 1
    for scale in (0.0, 0.001, 0.1, 1.0, 10.0, 1000.0):
        coefficient = analog.capacitive_reflection(scale / (z0 * cap), z0, cap)
        assert math.isclose(abs(coefficient), 1.0, abs_tol=1e-14)
        count += 1
record(258, count, '30 parameter sets:1,001 RK4 ODE samples each, voltage/current boundary identities, and180 frequency-domain magnitude checks.',
       'Declared capacitor-terminated lossless-line model, matched source, zero initial voltage. No missing-topology reconstruction, SPICE, threshold classification or hardware test.')


# Independent grid relaxation: an enclosed charge-free cavity with constant wall
# potential converges to that constant regardless of a circular/square mask.
rng = random.Random(271259)
count = 0
max_residual = 0.0
for size, shape, wall in itertools.product((13, 17, 21), ('square', 'circle'), (-2.0, 0.0, 1.0)):
    center = (size - 1) / 2
    radius = center - 1
    def inside(x, y, size=size, shape=shape, center=center, radius=radius):
        return 0 < x < size - 1 and 0 < y < size - 1 and (
            shape == 'square' or (x - center) ** 2 + (y - center) ** 2 < radius ** 2)
    grid = [[wall + rng.uniform(-1, 1) if inside(x, y) else wall for x in range(size)] for y in range(size)]
    for iteration in range(10000):
        change = 0.0
        for y in range(1, size - 1):
            for x in range(1, size - 1):
                if inside(x, y):
                    value = (grid[y - 1][x] + grid[y + 1][x] + grid[y][x - 1] + grid[y][x + 1]) / 4
                    change = max(change, abs(grid[y][x] - value))
                    grid[y][x] = value
        if change < 1e-13:
            break
    else:
        raise AssertionError('cavity relaxation did not converge')
    residual = max(abs(value - wall) for row in grid for value in row)
    max_residual = max(max_residual, residual)
    assert residual < 1e-10
    count += 1
for radius, outer_ratio, eps in itertools.product((0.001, 0.01, 1.0), (1.2, 2.0, 10.0), (analog.EPSILON_0, 4 * analog.EPSILON_0)):
    expected_voltage = 0.0
    # Integrate E(r)=lambda/(2*pi*eps*r) with midpoint quadrature.
    samples = 10000
    step = (outer_ratio * radius - radius) / samples
    for i in range(samples):
        expected_voltage += step / (2 * math.pi * eps * (radius + (i + 0.5) * step))
    computed = analog.outer_coax_capacitance_per_length(radius, outer_ratio * radius, eps)
    assert math.isclose(computed, 1 / expected_voltage, rel_tol=1e-7)
    count += 1
record(259, count, '18 circular/square finite-difference cavity relaxations with constant walls, plus18 exterior coax capacitance comparisons against10,000-cell radial field integration.',
       'The uniqueness theorem supplies the general result; finite grids illustrate it only. The external coax ground is an explicit example, not inferred source geometry.', maximum_cavity_potential_error=max_residual)


count = 0
for na, nd, intrinsic, temperature, voltage in itertools.product((1e21, 1e22, 1e23), (1e21, 1e22, 1e23), (1e15, 1e16), (280.0, 300.0, 320.0), (-2.0, -0.1, 0.0, 0.1)):
    eps = 11.7 * analog.EPSILON_0
    data = analog.abrupt_junction(na, nd, intrinsic, eps, temperature, voltage)
    xp, xn = data['p_width'], data['n_width']
    assert math.isclose(na * xp, nd * xn, rel_tol=1e-13)
    # Triangle field areas, calculated independently on each side.
    potential = analog.Q / (2 * eps) * (na * xp * xp + nd * xn * xn)
    assert math.isclose(potential, data['built_in_voltage'] - voltage, rel_tol=1e-13)
    assert math.isclose(data['field_peak'], analog.Q * na * xp / eps, rel_tol=1e-13)
    reverse = analog.abrupt_junction(na, nd, intrinsic, eps, temperature, voltage - 0.1)
    assert reverse['width'] > data['width']
    assert reverse['capacitance_per_area'] < data['capacitance_per_area']
    count += 1
record(260, count, '216 abrupt-junction parameter cases:depletion-charge neutrality, triangular-field potential integral, matching peak fields and monotone width/capacitance under more reverse bias.',
       'Ideal SI-unit depletion-approximation equations only. Material intrinsic concentration is a supplied independent parameter, not predicted versus temperature. No device simulation, breakdown model or measured diode curve.')


class Instrument:
    def __init__(self, values):
        self.values = values
        self.position = None
        self.gets = 0

    def set(self, position):
        assert type(position) is int and 0 <= position < len(self.values)
        self.position = position

    def get(self):
        self.gets += 1
        return self.values[self.position]


count = 0
arbitrary = 0
for n in range(1, 9):
    for values in itertools.product(range(3), repeat=n):
        device = Instrument(values)
        index, value = focus.scan_global_maximum(n, device.set, device.get)
        assert index == values.index(max(values)) and value == max(values)
        assert device.position == index and device.gets == n
        count += 1
        arbitrary += 1
unimodal = 0
for n in range(1, 81):
    for first_peak in range(n):
        for last_peak in {first_peak, n - 1, min(n - 1, first_peak + 1)}:
            values = tuple(i if i < first_peak else first_peak if i <= last_peak else first_peak - (i - last_peak) for i in range(n))
            device = Instrument(values)
            index, value = focus.unimodal_maximum(n, device.set, device.get)
            assert index == first_peak and value == max(values) and device.position == index
            assert device.gets <= 2 * math.ceil(math.log2(n)) + 1
            count += 1
            unimodal += 1
# Lower plateau demonstrates why ordinary weak unimodality is insufficient.
counterexample = (0, 0, 0, 1)
device = Instrument(counterexample)
wrong, _ = focus.unimodal_maximum(len(counterexample), device.set, device.get)
assert counterexample[wrong] != max(counterexample)
device = Instrument((10 ** 500, 10 ** 501, -(10 ** 502)))
assert focus.scan_global_maximum(3, device.set, device.get) == (1, 10 ** 501)
count += 1
record(270, count, f'{arbitrary} exhaustive arbitrary sequences over0,1,2 at lengths1..8;{unimodal} promised strict-slope/maximum-plateau sequences at lengths1..80, with oracle query counts and final setting checked.',
       'Deterministic simulated callback instrument, no real optics or noisy measurements. Includes an explicit weak-unimodality counterexample outside the faster algorithm contract.', outside_contract_counterexample=list(counterexample))


count = 0
for n in range(9):
    for inventory in itertools.combinations_with_replacement(range(1, 7), n):
        reachable = {}
        # Independent oracle enumerates physical-index subsets, not DP states.
        for mask in range(1 << n):
            chosen = tuple(i for i in range(n) if mask & (1 << i))
            total = sum(inventory[i] for i in chosen)
            reachable[total] = min(reachable.get(total, n + 1), len(chosen))
        for target in range(17):
            chosen = coins.minimum_payment_indices(inventory, target)
            expected = reachable.get(target)
            assert (chosen is None) == (expected is None)
            if chosen is not None:
                assert len(chosen) == len(set(chosen)) == expected
                assert sum(inventory[i] for i in chosen) == target
                assert all(0 <= i < n for i in chosen)
            count += 1
for inventory, expected in [([120], 1), ([1] * 120, 120), ([60, 60], 2), ([50, 50, 20], 3), ([60], None), ([70, 50, 50], 2), ([6, 5, 5], None)]:
    chosen = coins.minimum_payment_indices(inventory, 120)
    assert (None if chosen is None else len(chosen)) == expected
    count += 1
assert len(coins.minimum_payment_indices([6, 5, 5], 10)) == 2
assert coins.minimum_payment_indices([60], 120) is None
record(271, count + 2, 'All nondecreasing physical-coin inventories of0..8coins valued1..6, everytarget0..16, independently enumerated subsets;120target examples, greedy failure and forbidden reuse cases.',
       'Parameterized positive-integer inventory model. No universal numeric answer for the source is asserted; runtime is pseudopolynomial in the supplied target.')


# Input contract failures are tracked independently of positive-case totals.
invalid = [lambda: analog.capacitive_line_step(1, 0, 1, 0),
           lambda: analog.capacitive_line_step(1, 1, 1, -1),
           lambda: analog.capacitive_reflection(-1, 1, 1),
           lambda: analog.outer_coax_capacitance_per_length(2, 1, 1),
           lambda: analog.abrupt_junction(1e22, 1e22, 1e16, 1e-10, 300, 100),
           lambda: analog.abrupt_junction(0, 1e22, 1e16, 1e-10, 300),
           lambda: focus.scan_global_maximum(0, None, None),
           lambda: focus.unimodal_maximum(True, None, None),
           lambda: focus.scan_global_maximum(1, lambda _: None, lambda: float('nan')),
           lambda: coins.minimum_payment_indices([0], 120),
           lambda: coins.minimum_payment_indices([True], 120),
           lambda: coins.minimum_payment_indices([1], -1)]
for callback in invalid:
    try:
        callback()
    except ValueError:
        pass
    else:
        raise AssertionError('invalid input accepted')
summary = {'status': 'passed', 'results': results, 'invalid_cases': len(invalid),
           'total_positive_checks': sum(r['checks'] for r in results.values()),
           'scope': 'Executed Python models and independent finite oracles only; no SPICE, HDL, synthesis, physical measurement or production browser run.'}
(ROOT / 'checks' / 'batch1107-concepts-verification.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
