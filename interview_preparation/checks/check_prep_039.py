"""Independent exhaustive finite-state certificates for PREP-039.

The oracle represents positions as tuples, generates all directed transitions
directly from source/target states, and uses Bellman-Ford, not the solver's
bitmask move generator or Dijkstra implementation.
"""

import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prep039", ROOT / "solutions/prep_039_bridge_torch.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def independent_graph(times):
    n = len(times)
    states = list(itertools.product((0, 1), repeat=n + 1))
    edges = []
    for source in states:
        for target in states:
            if source[-1] == target[-1]:
                continue
            changed = [i for i in range(n) if source[i] != target[i]]
            if len(changed) not in (1, 2):
                continue
            if any(source[i] != source[-1] or target[i] != target[-1] for i in changed):
                continue
            edges.append((source, target, max(times[i] for i in changed)))
    return states, edges


def oracle(times):
    states, edges = independent_graph(times)
    goal = (1,) * (len(times) + 1)
    remaining = {state: float("inf") for state in states}
    remaining[goal] = 0
    for _ in range(len(states) - 1):
        changed = False
        for source, target, cost in edges:
            proposed = cost + remaining[target]
            if proposed < remaining[source]:
                remaining[source] = proposed
                changed = True
        if not changed:
            break
    return states, edges, remaining


def expect_invalid(schedule):
    try:
        MODEL.check_schedule((1, 2, 4, 5), schedule)
    except ValueError:
        return
    raise AssertionError("Invalid schedule was accepted")


def verify():
    times = (1, 2, 4, 5)
    states, edges, potential = oracle(times)
    start = (0,) * 5
    goal = (1,) * 5
    assert potential[start] == 12 and potential[goal] == 0
    # A lower-bound certificate: summing each inequality along any legal path
    # yields 12 <= that path's cost, without assuming a fixed number of trips.
    finite_edges = 0
    for source, target, cost in edges:
        assert potential[source] <= cost + potential[target]
        if potential[source] != float("inf"):
            assert potential[target] != float("inf")
            finite_edges += 1
    optimum, computed_schedule = MODEL.shortest_crossing(times)
    assert optimum == MODEL.check_schedule(times, computed_schedule) == 12
    assert MODEL.check_schedule(times, MODEL.puzzle_schedule()) == 12
    assert len(MODEL.puzzle_schedule()) == 5
    assert not optimum <= 11
    assert optimum <= 12
    greedy = [MODEL.Crossing((0, 1), True, 2), MODEL.Crossing((0,), False, 1),
              MODEL.Crossing((0, 2), True, 4), MODEL.Crossing((0,), False, 1),
              MODEL.Crossing((0, 3), True, 5)]
    assert MODEL.check_schedule(times, greedy) == 13
    # Cover duplicates, ties, short instances, and the 1,2,5,10 classic variant.
    instances = 0
    for n in range(1, 5):
        for values in itertools.combinations_with_replacement(range(1, 7), n):
            _, _, expected = oracle(values)
            result, schedule = MODEL.shortest_crossing(values)
            assert result == expected[(0,) * (n + 1)], values
            assert MODEL.check_schedule(values, schedule) == result, values
            instances += 1
    assert MODEL.shortest_crossing((1, 2, 5, 10))[0] == 17
    assert MODEL.shortest_crossing((5, 1, 4, 2))[0] == 12
    # Replay error paths: no one, too many, duplicated person, wrong bank,
    # duration, missing final people, and impossible direction.
    invalid = [[], [MODEL.Crossing((), True, 0)],
               [MODEL.Crossing((0, 1, 2), True, 4)],
               [MODEL.Crossing((0, 0), True, 1)],
               [MODEL.Crossing((0, 9), True, 1)],
               [MODEL.Crossing((0,), False, 1)],
               [MODEL.Crossing((0, 1), True, 1)],
               [MODEL.Crossing((0, 1), True, 2), MODEL.Crossing((2,), False, 4)],
               [MODEL.Crossing((0, 1), True, 2)]]
    for schedule in invalid:
        expect_invalid(schedule)
    invalid_inputs = [(), (0,), (-1,), (True,), (1.5,), (1, "2")]
    for values in invalid_inputs:
        try:
            MODEL.shortest_crossing(values)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid times accepted")
    certificate = []
    for mask in range(16):
        row = {"right_bank_people": ["ABCD"[i] for i in range(4) if mask & (1 << i)]}
        for torch in (0, 1):
            state = tuple((mask >> i) & 1 for i in range(4)) + (torch,)
            row["torch_right" if torch else "torch_left"] = (
                None if potential[state] == float("inf") else potential[state])
        certificate.append(row)
    return {
        "question": "PREP-039", "status": "passed", "model": "positive integer crossing times; one torch; capacity two; slower pair speed",
        "state_count": len(states), "directed_legal_edges": len(edges),
        "finite_certificate_edge_inequalities_checked": finite_edges,
        "minimum_hours": 12, "battery_hours": 12, "witness_crossings": 5,
        "greedy_fastest_return_strategy_hours": 13,
        "independent_bellman_ford_instances": instances,
        "additional_classic_and_permuted_instances": 2,
        "invalid_schedules_rejected": len(invalid), "invalid_inputs_rejected": len(invalid_inputs),
        "lower_bound_certificate": certificate,
        "certificate_meaning": "h(goal)=0, h(start)=12 and h(s)<=cost(s,t)+h(t) on every legal edge. Summing along any complete schedule proves its total is at least 12. Null denotes an isolated impossible torch configuration.",
        "scope": "Exact finite-state verification and checked lower-bound certificate, not random sampling or a human expert review. No physical torch experiment or live-site interaction."
    }


if __name__ == "__main__":
    report = verify()
    path = ROOT / "checks/prep-039-verification.json"
    path.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8"))
    print(json.dumps({key: value for key, value in report.items() if key != "lower_bound_certificate"}))
