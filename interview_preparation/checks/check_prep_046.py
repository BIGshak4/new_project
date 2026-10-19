"""Independent possible-world checks; does not modify archive, DB or users."""
import importlib.util
import json
import random
from itertools import combinations, pairwise, permutations
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "solutions/prep_046_birthday_knowledge.py"
SPEC = importlib.util.spec_from_file_location("birthday046", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def worlds_oracle(candidates):
    """Use explicit indistinguishable-world sets, not Counter/group filtering."""
    worlds = set(candidates)
    def compatible(possible, world, field):
        return {other for other in possible if other[field] == world[field]}
    first = {world for world in worlds
             if len(compatible(worlds, world, 0)) > 1
             and all(len(compatible(worlds, other, 1)) > 1
                     for other in compatible(worlds, world, 0))}
    second = {world for world in first
              if len(compatible(worlds, world, 1)) > 1
              and len(compatible(first, world, 1)) == 1}
    third = {world for world in second
             if len(compatible(second, world, 0)) == 1}
    return tuple(tuple(sorted(stage)) for stage in (worlds, first, second, third))


def verify():
    counts = {"candidate_subsets": 0, "shuffled_orders": 0,
              "month_relabellings": 0, "day_relabellings": 0,
              "duplicate_guard": 0}
    def check(dates, kind):
        before = tuple(dates)
        actual = tuple(MODULE.birthday_stages(dates).values())
        assert actual == worlds_oracle(dates)
        assert tuple(dates) == before
        assert all(set(later) <= set(earlier) for earlier, later in pairwise(actual))
        counts[kind] += 1
    dates = MODULE.DATES
    original = MODULE.birthday_stages()
    assert [len(v) for v in original.values()] == [10, 5, 3, 1]
    assert original["after_chaim"] == ((7, 14), (7, 16), (8, 14), (8, 15), (8, 17))
    assert original["after_yoni"] == ((7, 16), (8, 15), (8, 17))
    assert original["after_final_chaim"] == ((7, 16),)
    for size in range(len(dates) + 1):
        for subset in combinations(dates, size):
            check(subset, "candidate_subsets")
    rng = random.Random(20261019)
    for _ in range(200):
        shuffled = list(dates)
        rng.shuffle(shuffled)
        check(shuffled, "shuffled_orders")
    for labels in permutations((5, 6, 7, 8)):
        mapping = dict(zip((5, 6, 7, 8), labels))
        check(tuple((mapping[m], d) for m, d in dates), "month_relabellings")
    for labels in permutations((14, 15, 16, 17, 18, 19)):
        mapping = dict(zip((14, 15, 16, 17, 18, 19), labels))
        check(tuple((m, mapping[d]) for m, d in dates), "day_relabellings")
    try:
        MODULE.birthday_stages(((5, 15), (5, 15)))
    except ValueError:
        counts["duplicate_guard"] += 1
    else:
        raise AssertionError("Duplicate candidates must be rejected")
    return {"question_id": "PREP-046", "status": "passed", "counts": counts,
            "total_cases": sum(counts.values()), "stage_sizes": [10, 5, 3, 1],
            "final_date_day_month": "16/07",
            "oracle": "Explicit indistinguishable possible-world sets for each public statement",
            "scope": "Finite-model verification under truthful/common-knowledge assumptions; not professional review or live-site clicking"}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
