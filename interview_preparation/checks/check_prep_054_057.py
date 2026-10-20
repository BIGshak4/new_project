"""Reachable aggregate state search for unknown-initial token protocols.

Symmetry reduction is exact for the safety property: contributors are identical
and grouped only by how many of their two tokens they have emitted. This search
does not assert fairness or put a bound on unbounded stochastic execution.
"""
from collections import deque
import importlib.util
import json
import random
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


Two = load("two_switch_model", "prep_054_two_switches.py").TwoSwitchProtocol
One = load("one_light_model", "prep_057_prisoners_one_light.py").OneLightProtocol


def exhaustive(m, mandatory):
    visited_total, transitions, terminal_total = 0, 0, 0
    initial_settings = [(s, d) for s in (0, 1) for d in ((0, 1) if mandatory else (0,))]
    for initial_signal, initial_dummy in initial_settings:
        # n0,n1,n2,signal,count,dummy. Contributions emitted = n1+2*n2.
        start = (m, 0, 0, initial_signal, 0, initial_dummy)
        seen, queue = {start}, deque([start])
        while queue:
            n0, n1, n2, s, c, d = state = queue.popleft()
            assert n0 + n1 + n2 == m
            assert c + s == n1 + 2 * n2 + initial_signal
            if c == 2 * m:
                assert n0 == 0  # Every contributor has signaled; hence all visited.
                terminal_total += 1
                continue
            assert c < 2 * m
            if not s:
                assert n0 + n1 > 0  # Fairness eventually enables productive progress.
            successors = []
            if s:  # Counter consumes exactly one token.
                successors.append((n0, n1, n2, 0, c + 1, d))
            else:
                successors.append((n0, n1, n2, s, c, 1-d if mandatory else d))
            for j, population in enumerate((n0, n1, n2)):
                if not population:
                    continue
                if not s and j < 2:
                    histogram = [n0, n1, n2]
                    histogram[j] -= 1
                    histogram[j+1] += 1
                    successors.append((*histogram, 1, c, d))
                else:
                    successors.append((n0, n1, n2, s, c, 1-d if mandatory else d))
            for nxt in successors:
                transitions += 1
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        visited_total += len(seen)
    return visited_total, transitions, terminal_total


def simulations(cls, n, mandatory):
    runs, maximum_visits = 0, 0
    for initial in (False, True):
        for dummy in ((False, True) if mandatory else (False,)):
            for seed in range(100):
                rng = random.Random(seed)
                protocol = cls(n=n, signal=initial, dummy=dummy) if mandatory else cls(n=n, light=initial)
                seen = set()
                emitted = 0
                for visits in range(1, 200_001):
                    p = rng.randrange(n)
                    old_signal = protocol.signal if mandatory else protocol.light
                    old_dummy = protocol.dummy if mandatory else False
                    old_contributions = sum(protocol.contributions)
                    seen.add(p)
                    _, done = protocol.visit(p)
                    new_signal = protocol.signal if mandatory else protocol.light
                    if mandatory:
                        assert int(old_signal != new_signal) + int(old_dummy != protocol.dummy) == 1
                    emitted += sum(protocol.contributions) - old_contributions
                    assert protocol.observed + int(new_signal) == emitted + int(initial)
                    assert all(0 <= x <= 2 for x in protocol.contributions)
                    if done:
                        assert len(seen) == n
                        assert all(protocol.contributions[p] >= 1 for p in range(1, n))
                        runs += 1
                        maximum_visits = max(maximum_visits, visits)
                        break
                else:
                    raise AssertionError("Seeded simulation did not terminate within its test cap")
    return runs, maximum_visits


def run():
    # Explicit counterexample to the tempting one-token, unknown-initial strategy.
    # Initial ON -> counter counts 1; only contributor 1 signals; counter counts 2.
    # With 3 prisoners, threshold 2 would declare despite contributor 2 never visiting.
    naive_counterexample = {"n": 3, "initial_on": True, "visits": [0, 1, 0], "unvisited": [2]}
    for ident, m, mandatory, cls in (("PREP-054", 16, True, Two), ("PREP-057", 20, False, One)):
        states, transitions, terminals = exhaustive(m, mandatory)
        runs, max_visits = simulations(cls, m+1, mandatory)
        result = {
            "question_id": ident, "status": "passed", "contributors": m, "threshold": 2*m,
            "exhaustive_symmetric_reachable_states": states,
            "exhaustive_transitions": transitions, "safe_terminal_states": terminals,
            "seeded_individual_simulations": runs, "largest_test_visit_count": max_visits,
            "checked": ["all permitted initial switch states", "token conservation", "no unsafe declaration",
                        "at most two emissions per contributor", "mandatory exactly-one toggle" if mandatory else "optional unchanged visit",
                        "productive transition enabled in every nonterminal aggregate state"],
            "unsafe_naive_strategy_counterexample": naive_counterexample,
            "limits": "Aggregate safety search is exhaustive under contributor symmetry. Random simulations are finite examples, not a universal termination or time-bound proof. Fair infinite visitation is the separate assumption used in the written liveness proof. No physical experiment or human expert review.",
        }
        (BANK / "checks" / (ident.lower() + "-verification.json")).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
