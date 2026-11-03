"""Floyd-Warshall and interior-edge samples independently check shortest-path sums."""
import importlib.util
import itertools
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('street_reference', ROOT / 'solutions/prep_246_street_median.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run():
    checks = interior_checks = 0
    for n in range(1, 5):
        pairs = list(itertools.combinations(range(n), 2))
        for state in itertools.product((0, 1, 3), repeat=len(pairs)):
            edges = [(u, v, w) for (u, v), w in zip(pairs, state) if w]
            distances = [[None] * n for _ in range(n)]
            for u in range(n):
                distances[u][u] = 0
            for u, v, w in edges:
                distances[u][v] = distances[v][u] = w
            for k in range(n):
                for u in range(n):
                    for v in range(n):
                        if distances[u][k] is not None and distances[k][v] is not None:
                            d = distances[u][k] + distances[k][v]
                            if distances[u][v] is None or d < distances[u][v]:
                                distances[u][v] = d
            for people in itertools.product(range(n), repeat=2):
                totals = [(sum(distances[p][v] for p in people), v) for v in range(n)
                          if all(distances[p][v] is not None for p in people)]
                expected = None if not totals else min(totals)[::-1]
                actual = module.street_meeting_point(n, edges, list(people))
                assert actual == expected
                checks += 1
                if actual is not None:
                    for u, v, length in edges:
                        if any(distances[p][u] is None for p in people):
                            continue
                        for fraction in (Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)):
                            x = fraction * length
                            cost = sum(min(distances[p][u] + x, distances[p][v] + length - x) for p in people)
                            assert cost >= actual[1]
                            interior_checks += 1
    grid_checks = 0
    for points in itertools.product(tuple(itertools.product(range(3), repeat=2)), repeat=3):
        point, cost = module.grid_meeting_point(points)
        oracle = min(sum(abs(a - x) + abs(b - y) for a, b in points)
                     for x in range(3) for y in range(3))
        assert cost == oracle
        grid_checks += 1
    invalid = [(0, [], [0]), (2, [(0, 1, 0)], [0]), (2, [(0, 2, 1)], [0]), (2, [], [])]
    for args in invalid:
        try:
            module.street_meeting_point(*args)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid graph accepted')
    result = {'question': 'PREP-246', 'graph_origin_cases': checks, 'interior_edge_samples': interior_checks,
              'grid_cases': grid_checks, 'invalid_cases': len(invalid), 'passed': True,
              'scope': 'all simple graphs through four vertices with absent/1/3 edges and two origins; finite interior samples support a separate concavity proof'}
    (ROOT / 'checks/prep-246-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    print(json.dumps(run()))
