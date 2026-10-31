"""Independent finite oracles for the 2026-10-31 reasoning intake."""

import importlib.util
import itertools
import json
from collections import Counter, deque
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(stem):
    spec = importlib.util.spec_from_file_location(stem, HERE.parent / "solutions" / (stem + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def animal_oracle(*, relaxed, allow_no_sheep):
    # Six distinct identities and bank membership, independently of count transitions.
    edges, states = set(), set()
    for mask in range(64):
        banks = [[i for i in range(6) if ((mask >> i) & 1) == side] for side in (0, 1)]
        safe = True
        for bank in banks:
            wolves, sheep = sum(i < 3 for i in bank), sum(i >= 3 for i in bank)
            if wolves > sheep and not (allow_no_sheep and sheep == 0):
                safe = False
        if not safe:
            continue
        for boat in (0, 1):
            state = (mask, boat)
            states.add(state)
            sizes = (1, 2) if relaxed else ((2,) if boat == 0 else (1,))
            for size in sizes:
                for passengers in itertools.combinations(banks[boat], size):
                    new_mask = mask
                    for animal in passengers:
                        new_mask ^= 1 << animal
                    far_wolves = sum((new_mask >> i) & 1 for i in range(3))
                    far_sheep = sum((new_mask >> i) & 1 for i in range(3, 6))
                    tests = ((far_wolves, far_sheep), (3 - far_wolves, 3 - far_sheep))
                    if all(w <= s or (allow_no_sheep and s == 0) for w, s in tests):
                        edges.add((state, (new_mask, 1 - boat)))
    graph = {state: [] for state in states}
    for source, target in edges:
        graph[source].append(target)
    distance = {(0, 0): 0}
    queue = deque(distance)
    while queue:
        state = queue.popleft()
        for target in graph[state]:
            if target not in distance:
                distance[target] = distance[state] + 1
                queue.append(target)

    def counts(state):
        mask, boat = state
        return (sum((mask >> i) & 1 for i in range(3)), sum((mask >> i) & 1 for i in range(3, 6)), boat)

    quotient_states = {counts(state) for state in states}
    quotient_edges = {(counts(source), counts(target)) for source, target in edges}
    quotient_distances = {}
    for state, cost in distance.items():
        aggregate = counts(state)
        quotient_distances[aggregate] = min(cost, quotient_distances.get(aggregate, cost))
    return quotient_states, quotient_edges, quotient_distances


def check203():
    model = load("prep_203_wolves_sheep")
    modes = {}
    for relaxed, exception in itertools.product((False, True), repeat=2):
        actual = model.analyze(relaxed=relaxed, allow_no_sheep=exception)
        expected_states, expected_edges, expected_distances = animal_oracle(relaxed=relaxed, allow_no_sheep=exception)
        graph = actual["graph"]
        assert set(graph) == expected_states
        assert {(source, target) for source in graph for target, _ in graph[source]} == expected_edges
        assert actual["distance"] == expected_distances
        route = actual["route"]
        if not relaxed or not exception:
            assert route is None
        else:
            assert len(route) == 7 and route[-1][-1][1] == 3
            assert len(model.analyze(relaxed=True, all_animals=True)["route"]) == 11
            assert any(sum(passengers) == 2 and source[2] == 1 for source, passengers, _ in route)
        modes[f"{'relaxed' if relaxed else 'literal'}_{'zero_sheep_exception' if exception else 'strict_inequality'}"] = {
            "legal_count_states": len(graph), "legal_directed_edges": len(expected_edges),
            "reachable_count_states": len(expected_distances), "all_sheep_minimum_trips": None if route is None else len(route)}
    literal = model.analyze()
    assert set(literal["distance"]) == {(0, 0, 0), (1, 1, 1), (2, 0, 1), (1, 0, 0), (3, 0, 1), (2, 0, 0), (2, 2, 1)}
    assert sum(len(literal["graph"][state]) for state in literal["distance"]) == 7
    return {"status": "passed", "modes": modes, "literal_reachable_edges": 7,
            "relaxed_all_animals_minimum_trips": 11,
            "method": "Independent six-animal identity bitmask graph; compare every quotient state, legal edge and BFS distance with the count-state model in all four contracts. Literal reachable set is closed and has no all-sheep goal.",
            "limitation": "Exact finite river model; no-solution verdict depends on literal two-forward/one-back rule. Seven-trip solution explicitly relaxes both directions to one or two passengers and need not transport all wolves."}


def check206():
    model = load("prep_206_binary_divisibility")
    checks = 0
    for number in range(1 << 16):
        assert model.divisibility_2_4_8(number) == tuple(number % divisor == 0 for divisor in (2, 4, 8))
        for exponent in range(9):
            assert model.divisible_by_power_of_two(number, exponent) == (number % (2**exponent) == 0)
            checks += 1
    for number in (1 << 200, (1 << 200) + 8, (1 << 200) - 1, 0):
        for exponent in (0, 1, 2, 3, 199, 200, 201):
            assert model.divisible_by_power_of_two(number, exponent) == (number % (2**exponent) == 0)
            checks += 1
    assert model.divisibility_2_4_8(0) == (True, True, True)
    return {"status": "passed", "all_unsigned_16_bit_inputs": 65536, "general_exponent_comparisons": checks,
            "method": "Direct independent remainder oracle for all 16-bit numbers and exponents 0..8, plus high-precision boundary numbers and exponents around their width.",
            "limitation": "Nonnegative binary integers; no claim that unsigned bit tests define parsing, BCD or fractional-number semantics."}


def check162():
    model = load("prep_162_array_combinations_batch21")
    arrays = permutations = subsets = 0
    for length in range(7):
        for data in itertools.product((0, 1, 2), repeat=length):
            produced = list(model.distinct_array_permutations(data))
            expected = set(itertools.permutations(data))
            assert len(produced) == len(expected) and set(produced) == expected
            actual_subsets = list(model.positional_subsets(data))
            expected_subsets = Counter(subset for size in range(length + 1) for subset in itertools.combinations(data, size))
            assert Counter(actual_subsets) == expected_subsets
            assert len(actual_subsets) == 2**length
            permutations += len(produced)
            subsets += len(actual_subsets)
            arrays += 1
    data = [1, "a", (2,), 1]
    original = data.copy()
    assert set(model.distinct_array_permutations(data)) == set(itertools.permutations(data))
    assert data == original
    assert list(model.distinct_array_permutations([])) == [()]
    assert list(model.positional_subsets([])) == [()]
    assert len(list(model.distinct_array_permutations([1, 1, 2]))) == 3
    assert len(list(model.positional_subsets([1, 1, 2]))) == 8
    return {"status": "passed", "arrays_exhaustively_checked": arrays,
            "distinct_permutations_checked": permutations, "positional_subsets_checked": subsets,
            "method": "Every array over three integer values through length six versus independent itertools permutation sets and combination multisets; mixed hashable values, duplicates, empty outputs and input preservation checked.",
            "limitation": "Permutations deduplicate equal hashable values; subsets distinguish source positions and preserve input order, so repeated value-tuples are intentional. The source word combinations is not silently assigned one meaning."}


def check081():
    model = load("prep_081_error_time_window_batch21")
    streams = observations = 0
    for length in range(7):
        for timestamps in itertools.combinations_with_replacement((0, 1, 4, 9, 10, 11, 20), length):
            for reports in itertools.product((0, 1), repeat=length):
                for closed in (False, True):
                    monitor = model.ErrorTimeWindow(window_ns=10, closed_left=closed)
                    history = []
                    for report, now in zip(reports, timestamps):
                        if report:
                            history.append(now)
                        active = sum((t >= now - 10 if closed else t > now - 10) and t <= now for t in history)
                        assert monitor.observe(report, now) == (active >= 5)
                        assert len(monitor.errors) <= 5
                        observations += 1
                    streams += 1
    for closed, expected in ((False, False), (True, True)):
        monitor = model.ErrorTimeWindow(closed_left=closed)
        for t in (0, 1, 2, 3):
            assert not monitor.observe(1, t)
        assert monitor.observe(1, model.TEN_SECONDS_NS) == expected
    monitor = model.ErrorTimeWindow()
    assert [monitor.observe(1, 0) for _ in range(6)] == [False] * 4 + [True, True]
    assert not monitor.observe(0, model.TEN_SECONDS_NS)
    events = iter([1, 0, 1, 1, 1, 1])
    times = iter([0, 1, 2, 3, 4, 5])
    assert model.wait_for_error_threshold(events.__next__, times.__next__) == 5
    return {"status": "passed", "event_streams_checked": streams, "observations_checked": observations,
            "boundary_conventions": ["(t-10,t]", "[t-10,t]"], "threshold": "at least five distinct reports",
            "method": "Enumerate every binary-report stream through length six with every nondecreasing timestamp tuple from seven boundary-focused times. Compare every observation with full-history counting under both endpoint conventions; actual nanosecond boundary, six simultaneous reports and loop-stop behavior checked.",
            "limitation": "One report=one new incident, observed on a monotonic clock. Does not infer physical event times from a persistent level or delayed batch report. Ten-second boundary convention is explicit."}


CHECKS = {"203": check203, "206": check206, "162-array-batch21": check162, "081-time-batch21": check081}


def run(name):
    result = CHECKS[name]()
    (HERE / f"prep-{name}-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps({name: run(name) for name in CHECKS}, indent=2))
