"""Independent numeric/finite-domain checks for the October25 root-owned models."""

import importlib.util
import itertools
import json
import math
import random
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def model(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve their module through sys.modules.
    import sys

    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rc_checks():
    rc = model("prep_132_rc_coupled_inverters")
    rng = random.Random(132)
    cases = 0
    for tau in (0.2, 1.0, 5.0):
        for _ in range(20):
            start = rng.uniform(-1, 3)
            duration = tau * rng.uniform(0, 3)
            vdd = 1.0
            numerical = start
            steps = 1000
            dt = duration / steps
            for _ in range(steps):
                k1 = (vdd - numerical) / tau
                k2 = (vdd - (numerical + dt * k1 / 2)) / tau
                k3 = (vdd - (numerical + dt * k2 / 2)) / tau
                k4 = (vdd - (numerical + dt * k3)) / tau
                numerical += dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
            assert abs(rc.settle(start, duration, tau, vdd) - numerical) < 1e-10
            before_b = rng.uniform(0, 1)
            after_b = rng.uniform(0, 1)
            after = rc.capacitor_step(start, before_b, after_b)
            assert after - after_b == pytest.approx(start - before_b)
            cases += 1
    assert rc.pulse_end(0) == pytest.approx(math.log(2))
    points = rc.trace([(1, 1), (2, 0), (3, 1)], (0, 1, 1.5, 1 + math.log(2) + 1e-7, 2, 3))
    assert points[0] == (0, 1, 1, 0)
    assert points[1] == (1, 0, 0, 1)
    assert points[2][3] == 1 and points[3][3] == 0
    assert points[4][2] > 1 and points[4][3] == 0
    assert all(a + b == 1 for a, b, _, _ in points)
    for args in ((1, -1, 1, 1), (1, 1, 0, 1), (1, 1, 1, 0)):
        with pytest.raises(ValueError):
            rc.settle(*args)
    return {
        "rk4_interval_oracle_cases": cases,
        "rk4_steps_each": 1000,
        "continuity_cases": cases,
        "sampled_edge_cases": len(points),
        "first_isolated_pulse_tau_units": math.log(2),
        "scope": "Ideal unclamped RC/threshold model only; no SPICE, transistor or physical check.",
    }


def painter_checks():
    painter = model("prep_133_painter_sequences")
    for day in range(1001):
        a, b = painter.specified_positions(day)
        assert a == sum(2 for _ in range(day))
        assert b == 100 - sum(range(2, day + 2))
    assert [painter.specified_positions(i)[0] for i in range(3)] == [0, 2, 4]
    assert [painter.specified_positions(i)[1] for i in range(3)] == [100, 98, 95]
    assert painter.simultaneous_painted_door() == []
    a, no, yes = painter.two_compatible_continuations()
    assert no[:3] == yes[:3] == [100, 98, 95]
    assert all(x != y for x, y in zip(a, no, strict=True))
    assert [(i, x) for i, (x, y) in enumerate(zip(a, yes, strict=True)) if x == y] == [(4, 8)]
    assert painter.first_crossing() == (painter.Fraction(166, 15), painter.Fraction(332, 15))
    assert math.isqrt(849) ** 2 != 849
    return {
        "closed_form_vs_sum_cases": 1001,
        "compatible_prefixes_with_different_outcomes": 2,
        "conditional_recurrence_same_day_meetings": 0,
        "conditional_motion_crossing_time": "166/15",
        "conditional_motion_crossing_position": "332/15",
        "unconditional_source_answer": "underdetermined",
    }


def ecc_checks():
    ecc = model("prep_136_hamming_memory")
    codewords = [ecc.encode8(data) for data in range(256)]
    assert len(set(codewords)) == 256
    minimum = min((a ^ b).bit_count() for a, b in itertools.combinations(codewords, 2))
    assert minimum == 3
    sec_cases = 0
    for data, code in enumerate(codewords):
        assert ecc.syndrome12(code) == 0
        for position in range(13):
            received = code if position == 0 else code ^ (1 << (position - 1))
            restored, syndrome = ecc.decode12(received)
            assert restored == data and syndrome == position
            nearest = min(codewords, key=lambda candidate: (candidate ^ received).bit_count())
            assert nearest == code
            sec_cases += 1
    extended = [ecc.encode13(data) for data in range(256)]
    assert min((a ^ b).bit_count() for a, b in itertools.combinations(extended, 2)) == 4
    pairs = 0
    for data, code in enumerate(extended):
        assert ecc.decode13(code) == (data, "clean")
        for bit in range(13):
            assert ecc.decode13(code ^ (1 << bit)) == (data, "corrected")
        for first, second in itertools.combinations(range(13), 2):
            assert ecc.decode13(code ^ (1 << first) ^ (1 << second)) == (None, "double_error")
            pairs += 1
    example = codewords[0] ^ 1 ^ 2
    assert ecc.decode12(example)[0] != 0, "SEC alone can miscorrect a two-bit error"
    for value in (-1, 256, True, 1.5):
        with pytest.raises(ValueError):
            ecc.encode8(value)
    return {
        "payloads": 256,
        "sec_received_words": sec_cases,
        "independent_nearest_codeword_checks": sec_cases,
        "sec_minimum_distance": minimum,
        "extended_minimum_distance": 4,
        "extended_single_errors": 256 * 13,
        "extended_double_errors": pairs,
        "model": "at most one fault across data+four check bits; optional fifth overall parity detects pairs",
    }


def prisoner_checks():
    prison = model("prep_057_prisoners_one_light")
    runs = 0
    for n in (2, 3, 5, 21, 100):
        for initial in (False, True):
            protocol = prison.OneLightProtocol(n=n, light=initial)
            visited = set()
            done = False
            for _ in range(2 * n + 2):
                for visitor in range(n):
                    visited.add(visitor)
                    _, done = protocol.visit(visitor)
                    if done:
                        break
                if done:
                    break
            assert done and len(visited) == n and protocol.observed == 2 * (n - 1)
            runs += 1
    # Missing contributor99; every other contributor spends both allowances.
    p = prison.OneLightProtocol(n=100, light=True)
    p.visit(0)
    for visitor in range(1, 99):
        for _ in range(2):
            p.visit(visitor)
            p.visit(0)
    assert p.observed == 197 and p.contributions[99] == 0
    assert not p.visit(0)[1]
    return {
        "deterministic_fair_cyclic_runs": runs,
        "unknown_start_hundred_threshold": 198,
        "missing_contributor_counter_bound": 197,
        "known_off_threshold": 99,
        "termination_scope": "fair infinite visitation; no deterministic elapsed-visit bound",
    }


@pytest.mark.parametrize(
    "number,checker", [(132, rc_checks), (133, painter_checks), (136, ecc_checks), (57, prisoner_checks)]
)
def test_root_models_match_independent_oracles(number, checker):
    result = checker()
    assert result
    if number == 136:
        assert result["extended_double_errors"] == 19968


def write_results():
    for number, checker in (
        (132, rc_checks),
        (133, painter_checks),
        (136, ecc_checks),
        (57, prisoner_checks),
    ):
        stem = "prep-057-hundred-variant-verification" if number == 57 else f"prep-{number}-verification"
        (BANK / "checks" / (stem + ".json")).write_text(
            json.dumps(checker(), indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    write_results()
