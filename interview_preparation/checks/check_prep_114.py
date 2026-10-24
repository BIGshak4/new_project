"""Enumerate all small handshake graphs; construct and audit larger valid examples."""

import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("party", BANK / "solutions/prep_114_party_handshakes.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    graphs = valid = 0
    valid_by_guests = {}
    for guests in range(3):
        allowed = model.allowed_pairs(guests)
        valid_by_guests[guests] = 0
        for mask in range(1 << len(allowed)):
            edges = [pair for index, pair in enumerate(allowed) if mask & (1 << index)]
            # Separate neighbor sets reconstruct graph degrees independently.
            neighbors = [set() for _ in range(2 * (guests + 1))]
            for left, right in edges:
                neighbors[left].add(right)
                neighbors[right].add(left)
            counts = tuple(map(len, neighbors))
            assert model.degrees(guests, edges) == counts
            if len(set(counts[1:])) == len(counts) - 1:
                assert counts[1] == guests and counts[0] == guests
                assert sorted(counts[1:]) == list(range(2 * guests + 1))
                assert all(counts[a] + counts[b] == 2 * guests
                           for a, b in zip(range(2, len(counts), 2), range(3, len(counts), 2), strict=True))
                valid += 1
                valid_by_guests[guests] += 1
            graphs += 1
    constructed = 0
    for guests in range(21):
        edges = model.construct_example(guests)
        counts = model.degrees(guests, edges)
        assert model.satisfies_distinctness(guests, edges)
        assert counts[0] == counts[1] == guests
        assert sorted(counts[1:]) == list(range(2 * guests + 1))
        assert sum(counts) == 2 * len(edges)
        assert not any(a ^ 1 == b for a, b in edges)
        constructed += 1
    example = model.degrees(4, model.construct_example(4))
    assert len(example) == 10 and example[0] == example[1] == 4
    assert sorted(example[1:]) == list(range(9))
    assert model.complement_pairs(4) == ((0, 8), (1, 7), (2, 6), (3, 5))
    rejected = 0
    for edges in [[(0, 0)], [(0, 1)], [(0, 2), (2, 0)], [(0, 9)]]:
        try:
            model.degrees(1, edges)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(edges)
    return {"question_id": "PREP-114", "status": "passed", "all_small_graphs": graphs,
            "valid_small_graphs": valid, "valid_by_guest_couples": valid_by_guests,
            "constructed_larger_graphs": constructed, "constructed_guest_range": [0, 20],
            "four_guest_example_degrees": list(example), "invalid_graphs_rejected": rejected,
            "scope": "All simple nonpartner graphs for zero through two guest couples; valid family through twenty guest couples. General complement-peeling proof, not exhaustive enumeration, establishes the ten-person result."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-114-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
