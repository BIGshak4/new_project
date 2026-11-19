"""Exact finite checks of the proposed reasoning examples."""

import json
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path


def check_painter():
    scales = [Fraction(5, 4), Fraction(3, 2), Fraction(2), Fraction(7, 3)]
    widths = range(1, 10)
    cases = 0
    for model_scale, canvas_scale, model in product(scales, scales, widths):
        width = model * model_scale / canvas_scale
        assert width * canvas_scale == model * model_scale
        assert (width == model) == (model_scale == canvas_scale)
        cases += 1
    return {'exact_shared_and_differential_scale_cases': cases}


def check_commute():
    half_distance = Fraction(1, 2)
    free_speed = half_distance / 10
    slowed_speed = half_distance / 20
    assert free_speed / slowed_speed == 2
    assert half_distance / free_speed == 10
    scenarios = [[(20, slowed_speed)], [(10, 0), (10, free_speed)]]
    for scenario in scenarios:
        assert sum(t for t, _ in scenario) == 20
        assert sum(t * v for t, v in scenario) == half_distance
    assert half_distance / (slowed_speed * Fraction(5, 4)) == 16
    return {'equal_travel_times_with_distinct_stopped_minutes': [0, 10],
            'future_example_travel_minutes': [20, 10]}


def check_tokens():
    pairs = list(combinations(range(4), 2))
    for selected in pairs:
        assert sum(len(set(selected) & set(hidden_a)) == 1 for hidden_a in pairs) == 4
    weights = [Fraction(0), Fraction(1, 2), Fraction(1)]
    possible = [choice for choice in product(weights, repeat=4)
                if all(choice[i] + choice[j] == 1 for i, j in pairs)]
    assert possible == [(Fraction(1, 2),) * 4]
    return {'hidden_assignments': len(pairs), 'whole_selection_assignment_pairs': len(pairs) ** 2,
            'enumerated_half_increment_allocations': len(weights) ** 4}


if __name__ == '__main__':
    results = [check_painter(), check_commute(), check_tokens()]
    for ident, result in zip(range(374, 377), results, strict=True):
        output = Path(__file__).with_name(f'prep-{ident}-1118-verification.json')
        output.write_text(json.dumps({'status': 'passed', **result}, indent=2) + '\n', encoding='utf8')
    print(json.dumps(results))
