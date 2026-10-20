"""Exhaust the physical hypotheses independently of the decision-tree decoder."""
from fractions import Fraction
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("coins", ROOT / "solutions/prep_049_twelve_coins.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def physical_outcome(pans, odd, delta, normal=Fraction(100)):
    left, right = pans
    weights = {i: normal + (delta if i == odd else 0) for i in range(1, 13)}
    difference = sum(weights[i] for i in left) - sum(weights[i] for i in right)
    return "left" if difference > 0 else "right" if difference < 0 else "balance"


def verify():
    all_hypotheses = {(i, direction) for i in range(1, 13) for direction in ("heavy", "light")}
    traces = {}
    mass_cases = 0
    for odd, direction in sorted(all_hypotheses):
        for magnitude in (Fraction(1, 1000), Fraction(1), Fraction(99)):
            delta = magnitude if direction == "heavy" else -magnitude
            history, calls = [], []
            def balance(left, right):
                nonlocal calls
                assert len(left) == len(right) > 0
                assert len(set(left + right)) == len(left + right)
                assert set(left + right) <= set(range(1, 13))
                calls.append((left, right))
                result = physical_outcome((left, right), odd, delta)
                history.append(result)
                return result
            assert MODEL.identify(balance) == (odd, direction)
            assert len(calls) == 3
            mass_cases += 1
            if magnitude == 1:
                assert tuple(history) not in traces
                traces[tuple(history)] = (odd, direction)

    # Recompute all 27 leaves by filtering physical worlds, rather than trusting
    # any of the model's final-answer entries.
    impossible = []
    branch_sizes = {}
    for history in itertools.product(MODEL.OUTCOMES, repeat=3):
        candidates = set(all_hypotheses)
        for depth, outcome in enumerate(history):
            pans = MODEL.next_weighing(history[:depth])
            candidates = {(i, direction) for i, direction in candidates
                          if physical_outcome(pans, i, 1 if direction == "heavy" else -1) == outcome}
            if depth == 1:
                branch_sizes["/".join(history[:2])] = len(candidates)
        if candidates:
            assert len(candidates) == 1
            assert MODEL.diagnose(history) == next(iter(candidates))
        else:
            impossible.append(list(history))
            try:
                MODEL.diagnose(history)
            except ValueError:
                pass
            else:
                raise AssertionError("Impossible observation decoded as a real coin")
    assert len(traces) == 24 and len(impossible) == 3
    assert all(n <= 3 for n in branch_sizes.values())
    # A known-genuine reference is used only after its genuine status follows
    # from the first weighing: coins 1..8 on balance, 9..12 on imbalance.
    assert MODEL.SECOND["balance"][1] == (1, 2, 3)
    assert MODEL.SECOND["left"][1][-1] == MODEL.SECOND["right"][1][-1] == 9
    return {"question": "PREP-049", "status": "passed", "physical_mass_cases": mass_cases,
            "unique_hypotheses": 24, "exact_weighings_per_case": 3, "all_outcome_sequences": 27,
            "impossible_sequences_rejected": impossible, "hypotheses_after_second": branch_sizes,
            "two_weighing_capacity": 9, "three_weighing_capacity": 27,
            "scope": "Exact rational-weight simulation and independent possible-world filtering. No physical balance or professional human review."}


if __name__ == "__main__":
    report = verify()
    (ROOT / "checks/prep-049-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
