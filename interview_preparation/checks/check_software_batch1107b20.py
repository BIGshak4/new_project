"""Bounded deterministic software checks using structurally distinct oracles."""
import importlib.util
import itertools
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


def module(number, name):
    path = ROOT / "solutions" / f"prep_{number}_{name}_batch1107b20.py"
    spec = importlib.util.spec_from_file_location(f"prep{number}", path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def move_oracle(data, x, y):
    bits = [(byte >> bit) & 1 for byte in data for bit in range(8)]
    arc = [(x + step) % 1024 for step in range(y + 1)]
    before = [bits[i] for i in arc]
    after = before[1:] + before[:1]
    for index, bit in zip(arc, after):
        bits[index] = bit
    return [sum(bits[8 * i + bit] << bit for bit in range(8)) for i in range(128)]


def reverse_oracle(n):
    value = int(str(abs(n))[::-1]) * (-1 if n < 0 else 1)
    return value if -(1 << 31) <= value < (1 << 31) else 0


def relative_oracle(a1, a2):
    rank = {value: i for i, value in enumerate(a2)}
    return sorted(a1, key=lambda value: (0, rank[value]) if value in rank else (1, value))


def run():
    rng = random.Random(110720)
    move = module(278, "packed_move").move_bit
    reverse = module(285, "decimal_reverse").reverse_int32
    relative = module(287, "relative_sort").relative_sort
    lloyd = module(277, "kmeans").lloyd
    moves = 0
    for pattern in ([0] * 128, [255] * 128, [i * 37 % 256 for i in range(128)]):
        for x, y in itertools.product([0, 1, 7, 8, 1023], [0, 1, 7, 8, 1023]):
            actual = pattern[:]
            assert move(actual, x, y) is actual
            assert actual == move_oracle(pattern, x, y)
            moves += 1
    for _ in range(80):
        values = [rng.randrange(256) for _ in range(128)]
        x, y = rng.randrange(1024), rng.randrange(1024)
        actual = values[:]
        assert move(actual, x, y) == move_oracle(values, x, y)
        moves += 1
    invalid = 0
    for data, x, y in [([0] * 127, 0, 0), ([256] + [0] * 127, 0, 0),
                       ([0] * 128, -1, 0), ([0] * 128, 0, 1024)]:
        before = data[:]
        try:
            move(data, x, y)
            raise AssertionError("invalid input accepted")
        except ValueError:
            assert data == before
        invalid += 1
    numbers = [0, 1, -1, 10, -10, 120, -120, 12345, -12345,
               -(1 << 31), (1 << 31) - 1, 1463847412, -1463847412,
               1534236469, -1563847412] + [rng.randrange(-(1 << 31), 1 << 31) for _ in range(150)]
    for n in numbers:
        assert reverse(n) == reverse_oracle(n)
    sorts = 0
    a1, a2 = [2, 1, 2, 4, 6, 5, 9, 8, 3, 8, 7], [2, 1, 8, 3]
    assert relative(a1, a2) == [2, 2, 1, 8, 8, 3, 4, 5, 6, 7, 9]
    for _ in range(160):
        a1 = [rng.randrange(-5, 6) for _ in range(rng.randrange(30))]
        a2 = rng.sample(range(-7, 8), rng.randrange(10))
        original = (a1[:], a2[:])
        assert relative(a1, a2) == relative_oracle(a1, a2)
        assert (a1, a2) == original
        sorts += 1
    try:
        relative([1, 2], [1, 1])
        raise AssertionError("duplicate priority accepted")
    except ValueError:
        pass
    clustering = 0
    from fractions import Fraction

    def rational_step(points, indices):
        centers = [points[i] for i in indices]
        labels = [min(range(len(indices)), key=lambda j: sum((Fraction(a) - Fraction(b)) ** 2
                  for a, b in zip(point, centers[j]))) for point in points]
        means = []
        for j, center in enumerate(centers):
            group = [point for point, label in zip(points, labels) if label == j]
            means.append([sum(Fraction(point[d]) for point in group) / len(group)
                          for d in range(len(points[0]))] if group else list(center))
        return labels, means

    samples = [[(0, 0), (0, 2), (10, 10), (10, 12)], [(0, 0)] * 4,
               [(0, 0), (2, 0), (1, 0)]]
    samples += [[(rng.randrange(-8, 9), rng.randrange(-8, 9)) for _ in range(8)] for _ in range(32)]
    for points in samples:
        labels, centers = rational_step(points, [0, 1])
        result = lloyd(points, [0, 1], 1)
        assert result['labels'] == labels
        assert all(math.isclose(a, float(b), rel_tol=1e-12, abs_tol=1e-12)
                   for ca, cb in zip(result['centers'], centers) for a, b in zip(ca, cb))
        previous = float('inf')
        for budget in range(1, 9):
            result = lloyd(points, [0, 1], budget)
            assert result['sse'] <= previous + 1e-9
            previous = result['sse']
            if result['converged']:
                for point, label in zip(points, result['labels']):
                    distances = [sum((a - b) ** 2 for a, b in zip(point, center))
                                 for center in result['centers']]
                    assert distances[label] <= min(distances) + 1e-9
            clustering += 1
    expected = lloyd([(0, 0), (0, 2), (10, 10), (10, 12)], [0, 2])
    assert expected['labels'] == [0, 0, 1, 1] and expected['sse'] == 4
    assert expected['centers'] == [[0, 1], [10, 11]] and expected['converged']
    report = {
        'kind': 'executed-python-model-and-independent-oracles', 'passed': True,
        'PREP-278': {'positive_cases': moves, 'invalid_cases': invalid, 'oracle': 'snapshot unwrapped bit arc; rotate sequence then repack', 'same_list_identity': True},
        'PREP-285': {'positive_cases': len(numbers), 'oracle': 'decimal string reversal with independent int32 bounds'},
        'PREP-287': {'positive_cases': sorts + 1, 'invalid_cases': 1, 'oracle': 'rank-decorated full sort; candidate uses histogram', 'input_preserved': True},
        'PREP-277': {'rational_one_step_cases': len(samples), 'bounded_trajectory_checks': clustering,
                     'exact_demonstration': True, 'limits': 'Finite small integer coordinates; floating numerical model, not a global optimum proof or production clustering benchmark.'},
        'PREP-281': {'status': 'native_passed_separate_report', 'threads': 4, 'protected_increments': 100000,
                     'report': 'checks/batch1107b20-native-verification.json',
                     'not_claimed': 'No Python model claimed as C11 memory-model verification; bounded native stress is not a test of every interleaving or fairness.'},
    }
    (OUT / 'batch1107b20-software-verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for number in [277, 278, 285, 287]:
        (OUT / f'prep-{number}-batch1107b20-verification.json').write_text(json.dumps(report[f'PREP-{number}'], indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    run()
