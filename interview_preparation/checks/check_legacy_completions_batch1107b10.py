"""Independent finite oracles for the two explicitly selected completions."""
import importlib.util
import itertools
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_checks():
    painters = load("prep_133_explicit_painters_batch1107b10")
    payment = load("prep_271_concrete_inventory_batch1107b10")
    painter_checks = 0
    for last in range(1, 201):
        expected, a, b, step, day = [], 1, last, 2, 0
        while a <= last and b >= 1:
            expected.append((day, a, b))
            a += 2
            b -= step
            step += 1
            day += 1
        result = painters.analyze(last)
        assert result["visits"] == expected
        assert result["same_day"] == [(d, a) for d, a, b in expected if a == b]
        # Fractional interpolation is independently solved as two affine paths.
        crossing = result["continuous_crossing"]
        if crossing is not None:
            time, location = crossing
            if len(expected) == 1:
                assert time == 0 and location == expected[0][1] == expected[0][2]
                painter_checks += len(expected) + 2
                continue
            left_day = min(int(time), len(expected) - 2)
            _, a0, b0 = expected[left_day]
            _, a1, b1 = expected[left_day + 1]
            fraction = time - left_day
            assert 0 <= fraction <= 1
            assert a0 + fraction * (a1 - a0) == b0 + fraction * (b1 - b0) == location
        painter_checks += len(expected) + 2
    fixed = painters.analyze()
    assert fixed["same_day"] == [(11, 23)] and len(fixed["visits"]) == 13
    assert fixed["continuous_crossing"] == (Fraction(11), Fraction(23))
    assert 11 * 11 + 7 * 11 - 198 == 0

    coin_checks = 0
    for size in range(7):
        for coins in itertools.combinations_with_replacement(range(1, 6), size):
            by_sum = {}
            for mask in range(1 << size):
                indices = tuple(i for i in range(size) if mask & (1 << i))
                total = sum(coins[i] for i in indices)
                by_sum[total] = min(by_sum.get(total, size + 1), len(indices))
            for target in range(17):
                actual = payment.minimum_indices(coins, target)
                if target not in by_sum:
                    assert actual is None
                else:
                    assert len(actual) == len(set(actual)) == by_sum[target]
                    assert sum(coins[i] for i in actual) == target
                coin_checks += 1
    all_fixed = []
    for mask in range(1 << len(payment.COINS)):
        indices = [i for i in range(len(payment.COINS)) if mask & (1 << i)]
        if sum(payment.COINS[i] for i in indices) == payment.TARGET:
            all_fixed.append(indices)
    optimum = min(map(len, all_fixed))
    winners = [indices for indices in all_fixed if len(indices) == optimum]
    assert optimum == 3 and winners == [[1, 2, 3]]
    assert payment.completed_payment() == [1, 2, 3]
    assert all(sum(pair) != 120 for pair in itertools.combinations(payment.COINS, 2))
    remaining, greedy = payment.TARGET, []
    for index, value in enumerate(payment.COINS):
        if value <= remaining:
            remaining -= value
            greedy.append(index)
    assert greedy == [0, 4] and remaining == 5
    invalid = 0
    for func, args in [(painters.positions, (-1,)), (painters.positions, (True,)),
                       (painters.positions, (0, 0)), (payment.minimum_indices, ([0], 120)),
                       (payment.minimum_indices, ([True], 120)),
                       (payment.minimum_indices, ([1], -1))]:
        try:
            func(*args)
        except ValueError:
            invalid += 1
        else:
            raise AssertionError(args)
    return {"status": "passed", "checked_on": "2026-11-07",
            "painter_parameter_cases": 200, "painter_position_and_result_checks": painter_checks,
            "coin_inventory_target_cases": coin_checks, "fixed_coin_subsets": 64,
            "fixed_payment_minimum": 3, "fixed_payment_indices": [1, 2, 3],
            "fixed_painting_same_day_meetings": [[11, 23]],
            "fixed_continuous_crossing": {"day": "11", "position": "23"},
            "invalid_cases_rejected": invalid,
            "scope": "Executed exact Python models and independent finite oracles; not source reconstruction, physical experiment or human technical review."}


if __name__ == "__main__":
    result = run_checks()
    (ROOT / "checks/batch1107b10-legacy-completions-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
