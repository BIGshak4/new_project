"""Conservation witnesses and independent exhaustive integer-road transport."""

import importlib.util
import json
from collections import deque
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("camel_model", BANK / "solutions/prep_121_camel_bananas.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def exhaustive_integer_delivery(stock, capacity, distance):
    """All legal unit movements and local reload choices, with arbitrary caches.

    Each move consumes one whole banana; total stock strictly decreases, so
    this finite state search permits repeated/backward trips without cycles.
    It does not assume coalesced stock or the phase formula being checked.
    """
    initial = (0, 0, (stock,) + (0,) * distance)
    pending, seen = deque([initial]), {initial}
    best = stock if distance == 0 else 0
    while pending:
        position, cargo, caches = pending.popleft()
        if position == distance:
            best = max(best, cargo + caches[-1])
        locally_available = cargo + caches[position]
        for load in range(1, min(capacity, locally_available) + 1):
            after_caches = list(caches)
            after_caches[position] = locally_available - load
            for target in (position - 1, position + 1):
                if not 0 <= target <= distance:
                    continue
                after = (target, load - 1, tuple(after_caches))
                if after not in seen:
                    seen.add(after)
                    pending.append(after)
    return best, len(seen)


def run_checks():
    expected = Fraction(1600, 3)
    value, phases = model.continuous_optimum()
    assert value == expected
    assert [p["end"] for p in phases] == [200, expected, 1000]
    assert [p["consumption_per_km"] for p in phases] == [5, 3, 1]
    assert [p["stock_after"] for p in phases] == [2000, 1000, expected]
    continuous = model.canonical_plan()
    integer = model.canonical_plan(integer=True)
    assert continuous.caches[1000] == expected and continuous.discarded == 0
    assert continuous.eaten == Fraction(7400, 3)
    assert integer.caches[1000] == 533 and integer.eaten == 2466 and integer.discarded == 1
    for journey in (continuous, integer):
        assert journey.position == 1000 and journey.cargo == 0
        assert sum(journey.caches.values()) + journey.eaten + journey.discarded == 3000
        assert len([event for event in journey.log if event[0] == "move"]) == 9
        assert max(event[3] for event in journey.log) <= 1000
    assert all(value.denominator == 1 for event in integer.log for value in event[1:])
    # The cut-crossing lower bound in the proof, inverted algebraically.
    assert Fraction(1000, 3) + 5 * expected == 3000
    assert Fraction(1000, 3) + 5 * (expected + Fraction(1, 1000)) > 3000
    assert expected < 534 and integer.caches[1000] == expected.numerator // expected.denominator
    cases = states = exact_relaxation_matches = 0
    for capacity in range(1, 4):
        for stock in range(3 * capacity + 1):
            for distance in range(5):
                actual, explored = exhaustive_integer_delivery(stock, capacity, distance)
                relaxed, _ = model.continuous_optimum(stock, capacity, distance)
                assert actual <= relaxed  # Integer schedules are a subset of the relaxation.
                if relaxed.denominator == 1:
                    assert actual == relaxed
                    exact_relaxation_matches += 1
                cases += 1
                states += explored
    assert exhaustive_integer_delivery(0, 1, 3)[0] == 0
    assert exhaustive_integer_delivery(3, 3, 2)[0] == 1
    rejected = 0
    for args in ((-1, 1, 1), (1, 0, 1), (1, 1, -1)):
        try:
            model.continuous_optimum(*args)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(args)
    return {"question_id": "PREP-121", "status": "passed", "continuous_delivery": "1600/3",
            "whole_banana_delivery": 533, "canonical_plan_move_legs_each": 9,
            "canonical_conservation_events": len(continuous.log) + len(integer.log),
            "small_integer_road_cases": cases, "exhaustively_explored_states": states,
            "integer_relaxation_equalities": exact_relaxation_matches, "invalid_cases_rejected": rejected,
            "scope": "Exact Fraction phases, explicit bidirectional cache/cargo conservation witnesses, independent exhaustive small integer-road states. General optimality follows the written cut-crossing proof, not finite examples."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-121-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
