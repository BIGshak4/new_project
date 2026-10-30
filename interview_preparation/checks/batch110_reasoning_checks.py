"""Independent exact finite oracles for batch110 reasoning content."""

import importlib.util
import itertools
import json
import math
from collections import Counter
from fractions import Fraction
from heapq import heappop, heappush
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(stem):
    spec = importlib.util.spec_from_file_location(stem, HERE.parent / "solutions" / (stem + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_190():
    model = load("prep_190_voting_agenda")
    rankings = list(itertools.permutations("ABC"))
    compatible = []
    first_tied_profiles = 0
    # Independently enumerate all first-choice-tied profiles, not just model family.
    for x, z, v in itertools.product(range(38), repeat=3):
        counts = (x, 37 - x, z, 37 - z, v, 37 - v)
        approval = Counter()
        for ranking, count in zip(rankings, counts):
            approval.update({candidate: count for candidate in ranking[:2]})
        first_tied_profiles += 1
        if len(set(approval.values())) != 1:
            continue
        profile = dict(zip(rankings, counts))
        assert profile == model.tied_profile(x)
        compatible.append(profile)
        voters = [ranking for ranking, count in profile.items() for _ in range(count)]
        for first, second in itertools.combinations("ABC", 2):
            expected = sum(voter.index(first) < voter.index(second) for voter in voters)
            assert model.pairwise_votes(profile, first, second) == (expected, 111 - expected)
            assert expected != 111 - expected
        for bye in "ABC":
            assert model.agenda_winner(profile, bye) == bye
    assert len(compatible) == 38
    first, approval = model.ballot_totals(model.tied_profile(37))
    assert first == {"A": 37, "B": 37, "C": 37}
    assert approval == {"A": 74, "B": 74, "C": 74}
    return {"status": "passed", "first_choice_tied_profiles_enumerated": first_tied_profiles,
            "profiles_compatible_with_both_ties": len(compatible), "bye_agendas_checked": 114,
            "method": "Independent full enumeration of the 38^3 first-choice-tied profiles; retain equal approval totals, expand individual strict ballots and compare every pair and all three agendas.",
            "limitation": "Assumes fixed strict rankings, equal-weight first/second approvals and sincere majority runoff votes. Does not define a universal normative fairness criterion."}


def check_192():
    model = load("prep_192_bench_probability")
    records, arrangements = [], 0
    for n in range(2, 9):
        immediate = anywhere = total = 0
        for seating in itertools.permutations(range(n)):
            c, f = seating.index(0), seating.index(1)
            immediate += f == c + 1
            anywhere += f > c
            total += 1
        assert model.right_of_probabilities(n) == (Fraction(immediate, total), Fraction(anywhere, total))
        records.append({"n": n, "arrangements": total, "immediate_right": immediate, "anywhere_right": anywhere})
        arrangements += total
    six = records[4]
    assert six == {"n": 6, "arrangements": 720, "immediate_right": 120, "anywhere_right": 360}
    return {"status": "passed", "arrangements_enumerated": arrangements, "widths": "2..8", "six_people": six,
            "method": "Every seating permutation enumerated independently; positions compared directly, exact rational probabilities versus block/symmetry formulas.",
            "limitation": "Uniform random linear seating of distinct people; not a circular bench or a conditional-on-C-at-a-known-end problem."}


def check_195():
    model = load("prep_195_helper_swap_boxes")
    cases = queries = 0
    maximum = 0
    for n in range(1, 9):
        limit = (n + 1) // 2
        for permutation in itertools.permutations(range(1, n + 1)):
            prepared, swap = model.prepare_boxes(permutation, limit)
            changed = [i for i in range(n) if prepared[i] != permutation[i]]
            assert len(changed) in (0, 2)
            assert (swap is None) == (not changed)
            assert sorted(prepared) == list(range(1, n + 1))
            for target in range(1, n + 1):
                log = []

                def read_note(box, log=log, prepared=prepared):
                    log.append(box)
                    return prepared[box - 1]

                count = model.find_target(read_note, target, limit, n)
                assert count == len(log) <= limit
                assert len(set(log)) == count
                assert prepared[log[-1] - 1] == target
                queries += count
                maximum = max(maximum, count)
            cases += 1
    # All 100 targets in structured original permutations with every long-cycle length.
    large_cases = 0
    for long_length in range(51, 101):
        original = list(range(2, long_length + 1)) + [1] + list(range(long_length + 1, 101))
        prepared, swap = model.prepare_boxes(original)
        assert swap is not None
        for target in range(1, 101):
            assert model.find_target(lambda box, prepared=prepared: prepared[box - 1], target) <= 50
        large_cases += 1
    identity, swap = model.prepare_boxes(list(range(1, 101)))
    assert swap is None and all(model.find_target(lambda box: identity[box - 1], t) == 1 for t in range(1, 101))
    # Wrong-direction controls: one untouched 100-cycle requires 100 queries.
    unprepared = list(range(2, 101)) + [1]
    try:
        model.find_target(lambda box: unprepared[box - 1], 1)
    except LookupError:
        pass
    else:
        raise AssertionError("The no-swap 100-cycle must fail within 50 opens")
    return {"status": "passed", "small_permutations_exhaustively_checked": cases,
            "actual_query_calls": queries, "small_maximum_opens": maximum,
            "hundred_box_long_cycle_cases": large_cases, "targets_per_hundred_box_case": 100,
            "method": "Exhaust every permutation at sizes 1..8; helper result differs at zero or two positions, then independently trace the read-only finder for every target. Also cover every long-cycle length 51..100 and an untouched 100-cycle failure control.",
            "limitation": "The source's boxes have explicit agreed labels and a permutation of distinct notes; at most one helper swap, known pointer-following agreement, no later communication. Proof covers all 100! arrangements; finite enumeration alone does not."}


def canoe_graph(times):
    n = len(times)
    states = list(itertools.product((0, 1), repeat=n + 1))
    edges = []
    for state in states:
        available = [i for i in range(n) if state[i] == state[-1]]
        for size in (1, 2):
            for group in itertools.combinations(available, size):
                new = list(state)
                for i in (*group, n):
                    new[i] ^= 1
                edges.append((state, tuple(new), max(times[i] for i in group)))
    return states, edges


def check_039_canoe():
    model = load("prep_039_canoe_batch110")
    total, timeline = model.replay_schedule()
    assert total == 28 and [line[-1] for line in timeline] == [3, 4, 15, 18, 24, 25, 28]
    states, edges = canoe_graph(model.TIMES)
    start, goal = (0,) * 6, (1,) * 6
    adjacency = {state: [] for state in states}
    for source, target, cost in edges:
        adjacency[source].append((target, cost))
    distances = {start: 0}
    heap = [(0, start)]
    while heap:
        cost, state = heappop(heap)
        if distances[state] != cost:
            continue
        for target, weight in adjacency[state]:
            new_cost = cost + weight
            if new_cost < distances.get(target, math.inf):
                distances[target] = new_cost
                heappush(heap, (new_cost, target))
    assert distances[goal] == total == 28
    assert total < 30
    # Independent Bellman-Ford over the complete edge list and a potential certificate.
    lower = {goal: 0}
    for _ in range(len(states) - 1):
        changed = False
        for source, target, weight in edges:
            candidate = lower.get(target, math.inf) + weight
            if candidate < lower.get(source, math.inf):
                lower[source] = candidate
                changed = True
        if not changed:
            break
    assert lower[start] == 28
    certified = 0
    for source, target, weight in edges:
        if source in lower and target in lower:
            assert lower[source] <= weight + lower[target]
            certified += 1
    return {"status": "passed", "witness_minutes": total, "strict_deadline_minutes": 30,
            "margin_minutes": 2, "state_count": len(states), "directed_edges": len(edges),
            "reachable_states": len(distances), "certificate_edges": certified,
            "cumulative_minutes": [line[-1] for line in timeline],
            "method": "Replay source-specific schedule; independently build all tuple-bank states and legal one/two-person moves. Full Dijkstra and reverse Bellman-Ford agree at 28; potential inequalities checked on every reachable edge give a lower bound for arbitrary-length schedules.",
            "limitation": "Exact deterministic positive crossing-time model, no overhead or physical trial. Strictly before 30 is satisfied; completion at exactly 30 would fail the source deadline."}


def check_198():
    model = load("prep_198_nested_uniform")
    checked = 0
    for upper in range(101):
        a_mass, b_mass = model.nested_marginals(upper)
        independent_a, independent_b = Counter(), Counter()
        for a in range(upper + 1):
            for b in range(a + 1):
                probability = Fraction(1, upper + 1) * Fraction(1, a + 1)
                assert model.joint_probability(a, b, upper) == probability
                independent_a[a] += probability
                independent_b[b] += probability
                checked += 1
        assert a_mass == [independent_a[a] for a in range(upper + 1)]
        assert b_mass == [independent_b[b] for b in range(upper + 1)]
        assert sum(a_mass) == sum(b_mass) == 1
        assert sum(Fraction(b) * probability for b, probability in enumerate(b_mass)) == Fraction(upper, 4)
        for b in range(upper):
            assert b_mass[b] - b_mass[b + 1] == Fraction(1, (upper + 1) * (b + 1))
    a_mass, b_mass = model.nested_marginals(100)
    assert sum(Fraction(b * b) * value for b, value in enumerate(b_mass)) - 25**2 == 500
    return {"status": "passed", "joint_cells_exactly_enumerated": checked, "upper_bounds": "0..100",
            "mass_sum_A": "1", "mass_sum_B": "1", "expected_A": "50", "expected_B": "25", "variance_B": "500",
            "B_zero_probability_decimal": float(b_mass[0]), "B_hundred_probability": str(b_mass[100]),
            "method": "Independent exact joint-table summation using Fraction for every upper bound 0..100; compare both marginals, normalization, adjacent mass differences and expected values.",
            "limitation": "Inclusive integer endpoints and conditional uniform draws. No empirical RNG test and no continuous-uniform approximation substituted for the discrete law."}


CHECKS = {"190": check_190, "192": check_192, "195": check_195, "198": check_198, "039-canoe-batch110": check_039_canoe}


def run(name):
    result = CHECKS[name]()
    (HERE / f"prep-{name}-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps({name: run(name) for name in CHECKS}, indent=2))
