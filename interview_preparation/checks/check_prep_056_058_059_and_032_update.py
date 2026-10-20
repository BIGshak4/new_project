"""Independent finite checks for the 2026-10-20 content additions.

This is Python-model verification, not HDL compilation/simulation or human
content approval. Run from any directory with Python 3.11+.
"""
import importlib.util
import itertools
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    path = ROOT / "solutions" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class HostileNode:
    def __init__(self, next_node=None):
        self.value = 7
        self.next = next_node

    def __eq__(self, other):
        raise AssertionError("must compare identity, never equality")


def chain(length, tail=None):
    for _ in range(length):
        tail = HostileNode(tail)
    return tail


def nodes(head):
    result = []
    while head is not None:
        result.append(head)
        head = head.next
    return result


def check_lists():
    fn = module("prep_032_head_switch_intersection").first_shared_node
    cases = 0
    for a, b, common in itertools.product(range(9), repeat=3):
        shared = chain(common)
        ha, hb = chain(a, shared), chain(b, shared)
        every = nodes(ha) + nodes(hb)
        snapshot = [(node, node.next, node.value) for node in every]
        for first, second in ((ha, hb), (hb, ha)):
            assert fn(first, second) is shared
            cases += 1
        assert all(node.next is nxt and node.value == value for node, nxt, value in snapshot)
    shared = chain(1)
    assert fn(chain(10000, shared), chain(3, shared)) is shared
    assert fn(chain(10001), chain(9999)) is None
    return {"identity_cases": cases, "long_cases": 2,
            "coverage": "All 729 private/private/shared length triples 0..8 in both argument orders; hostile equality, duplicate values, immutability, empty/disjoint/shared heads; two long cases."}


def check_enable():
    mod = module("prep_056_dff_enable")
    transitions = 0
    for q, data, en in itertools.product((0, 1), repeat=3):
        assert mod.next_q(q, data, en) == (data if en else q)
        transitions += 1
    streams = 0
    for initial in (0, 1):
        for length in range(7):
            for samples in itertools.product(tuple(itertools.product((0, 1), repeat=2)), repeat=length):
                expected, q = [], initial
                for data, en in samples:
                    if en:
                        q = data
                    expected.append(q)
                assert mod.trace(initial, samples) == expected
                streams += 1
    return {"transitions": transitions, "streams": streams,
            "coverage": "All 8 Boolean transitions; both initial states and every data/enable stream of length 0..6. No HDL simulator or physical timing/CDC check."}


def check_average():
    fn = module("prep_058_average_difference_two").average_gates
    counts = {}
    for width in range(2, 11):
        n = 0
        for a in range((1 << width) - 2):
            b = a + 2
            y = fn(a, b, width)
            assert y == (a + b) // 2
            assert 0 <= y < (1 << width)
            n += 1
        counts[str(width)] = n
    invalid = 0
    for args in ((0, 2, 1), (-1, 1, 3), (6, 0, 3), (0, 1, 3), (0, 2, 0), (True, 3, 2)):
        try:
            fn(*args)
        except ValueError:
            invalid += 1
        else:
            raise AssertionError(args)
    return {"valid_pairs": sum(counts.values()), "width_counts": counts, "invalid_cases": invalid,
            "coverage": "Exhaustive every valid unsigned pair for widths 2..10; independent arithmetic oracle; invalid relation, negative input, wrapped pair and invalid width rejection. No HDL compilation/simulation/synthesis."}


def check_coins():
    fn = module("prep_059_dark_coin_groups").blind_plan
    cases = 0
    for k in range(11, 17):
        ga, gb, flips = fn(k)
        assert set(ga).isdisjoint(gb) and set(ga) | set(gb) == set(range(k))
        assert ga and gb and flips == ga and len(ga) == 10
        for tails in itertools.combinations(range(k), 10):
            before = set(tails)
            after = before.symmetric_difference(flips)
            assert sum(i in after for i in ga) == sum(i in after for i in gb)
            cases += 1
    rng = random.Random(20261020)
    random_cases = 0
    for k in (17, 21, 50, 100, 1000):
        for _ in range(100):
            ga, gb, flips = fn(k)
            after = set(rng.sample(range(k), 10)).symmetric_difference(flips)
            assert sum(i in after for i in ga) == sum(i in after for i in gb)
            random_cases += 1
    generalization = 0
    for k in range(2, 11):
        for t in range(1, k):
            ga, gb, flips = fn(k, t)
            for tails in itertools.combinations(range(k), t):
                after = set(tails).symmetric_difference(flips)
                assert sum(i in after for i in ga) == sum(i in after for i in gb)
                generalization += 1
    return {"exhaustive_original_cases": cases, "random_cases": random_cases,
            "generalization_cases": generalization,
            "coverage": "Every placement of ten tails for k=11..16; 500 reproducible larger examples; all 0<t<k<=10 generalizations. Planner receives no orientations."}


if __name__ == "__main__":
    checks = {"032-update": check_lists(), "056": check_enable(), "058": check_average(), "059": check_coins()}
    for key, result in checks.items():
        path = ROOT / "checks" / f"prep-{key}-verification.json"
        path.write_text(json.dumps({"question_id": f"PREP-{key}", "checked_on": "2026-10-20", "status": "passed_python_model", **result}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(checks, indent=2))
