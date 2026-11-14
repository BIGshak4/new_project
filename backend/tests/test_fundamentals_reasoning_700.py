"""Input-derived, independent exact oracles for all 350 reasoning700 variants.

Answer checking never imports the authoring implementation. Small finite worlds,
recurrences, constructive bounds and exact rational arithmetic test the teaching
models. These are not measurements, human expert review or learner calibration.
"""

from __future__ import annotations

import calendar
import importlib.util
import itertools as it
import json
import re
from collections import deque
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
BATCH = ROOT / "backend/seeds/duel_quiz_batches"
CARDS = json.loads((CONTENT / "fundamentals-reasoning-700.json").read_bytes())
ROWS = json.loads((BATCH / "reasoning_700.json").read_bytes())
CHECKS = json.loads((BATCH / "reasoning_700.checks.json").read_bytes())
BY_KEY = {row["key"]: row for row in ROWS}


def inventory_states(values):
    """Incremental index-subset worlds; retains equal-valued identities."""
    states = [(0, 0, ())]
    for index, value in enumerate(values):
        states += [(total + value, size + 1, (*chosen, index)) for total, size, chosen in states]
    return states


def covered_endpoint(values):
    """Greedy interval invariant, unlike the author's exhaustive subset sums."""
    reach = 0
    for value in sorted(values):
        if value > reach + 1:
            break
        reach += value
    return reach


def shortest_paths(data):
    """Repeated edge relaxation, not the author's Floyd-Warshall matrix."""
    result = []
    for source in range(data["n"]):
        best = [None] * data["n"]
        best[source] = 0
        for _ in range(data["n"] - 1):
            old = list(best)
            for a, b, length in data["edges"]:
                for u, v in ((a, b), (b, a)):
                    if old[u] is not None and (best[v] is None or old[u] + length < best[v]):
                        best[v] = old[u] + length
        result.append(best)
    return result


def quality_worlds(data, count):
    """Enumerate source and all result sequences with exact product weights."""
    for source, prior, rate in ((0, F(data["prior"]), F(data["a"])), (1, 1 - F(data["prior"]), F(data["b"]))):
        for word in it.product((0, 1), repeat=count):
            weight = prior
            for good in word:
                weight *= rate if good else 1 - rate
            yield source, word, weight


def squared_assignment(value, centers):
    """Distance is nonnegative: absolute distance yields the same nearest center."""
    best = 0
    for index in range(1, len(centers)):
        if abs(value - centers[index]) < abs(value - centers[best]):
            best = index
    return best


def truth_models(data):
    """Enumerate subsets of true-variable indices rather than numeric bit tuples."""
    for selected in it.chain.from_iterable(
        it.combinations(range(data["n"]), k) for k in range(data["n"] + 1)
    ):
        true = set(selected)
        if all(not (a in true and b not in true) for a, b in data["rules"]) and all(
            (i in true) == bool(v) for i, v in data.get("known", [])
        ):
            yield true


def date_parts(value):
    return tuple(map(int, value.split("-")))


def next_day(parts):
    year, month, day = parts
    if day < calendar.monthrange(year, month)[1]:
        return year, month, day + 1
    if month < 12:
        return year, month + 1, 1
    return year + 1, 1, 1


def oracle(task, d):
    if task == "coin_min":
        # 0/1 dynamic programming, copied per coin to forbid reuse.
        best = {0: 0}
        for coin in d["coins"]:
            nxt = dict(best)
            for total, count in best.items():
                nxt[total + coin] = min(nxt.get(total + coin, count + 1), count + 1)
            best = nxt
        return best.get(d["target"], -1)
    if task == "coin_ways":
        ways = {0: 1}
        for coin in d["coins"]:
            updated = dict(ways)
            for total, count in ways.items():
                updated[total + coin] = updated.get(total + coin, 0) + count
            ways = updated
        return ways.get(d["target"], 0)
    if task == "coverage_gap":
        return covered_endpoint(d["weights"]) + 1
    if task == "lost_weight":
        endpoints = []
        for lost in range(len(d["weights"])):
            remain = [w for i, w in enumerate(d["weights"]) if i != lost]
            endpoints.append(covered_endpoint(remain))
        return min(endpoints)
    if task == "extend_coverage":
        r = d["covered"]
        good = []
        for weight in range(1, 2 * r + 4):
            attainable = set(range(r + 1)) | {x + weight for x in range(r + 1)}
            if attainable == set(range(r + weight + 1)):
                good.append(weight)
        return max(good)
    if task == "weight_bound":
        # Capacity lower bound plus explicit powers-of-two coverage witness.
        pieces, states = [], {0}
        while not set(range(d["target"] + 1)) <= states:
            weight = max(states) + 1
            pieces.append(weight)
            states |= {x + weight for x in list(states)}
        assert 2 ** (len(pieces) - 1) < d["target"] + 1 <= len(states)
        return len(pieces)
    if task == "signed_weights":
        reachable = {0}
        for weight in d["weights"]:
            old = set(reachable)
            reachable |= {x + weight for x in old} | {x - weight for x in old}
        return sum(x > 0 for x in reachable)
    if task == "gold_cuts":
        # Exhaust all nondecreasing integral partitions of the whole small bar.
        def partitions(remaining, least=1):
            if remaining == 0:
                yield ()
            for piece in range(least, remaining + 1):
                for suffix in partitions(remaining - piece, piece):
                    yield (piece, *suffix)

        return min(len(parts) - 1 for parts in partitions(d["days"]) if covered_endpoint(parts) == d["days"])
    if task == "gold_exchange":
        weights = [2**i for i in range(d["power"] + 1)]
        states = inventory_states(weights)
        before = next(set(chosen) for total, _, chosen in states if total == d["before"])
        after = next(set(chosen) for total, _, chosen in states if total == d["after"])
        return len(before - after) + len(after - before)
    if task == "gold_no_change":
        # Each day's new payment uses disjoint material and has positive size 1.
        pieces = [1 for _ in range(d["days"])]
        assert sum(pieces) == d["days"]
        count, cuts = 1, 0
        while count < len(pieces):
            count += 1
            cuts += 1
        return cuts
    if task == "factory_posterior":
        positive_a, positive_all = F(), F()
        for source, quality, weight in quality_worlds(d, 1):
            positive_probability = F(d["sensitivity"] if quality[0] else d["false_positive"])
            positive_all += weight * positive_probability
            if source == 0:
                positive_a += weight * positive_probability
        return positive_a / positive_all
    if task in {"factory_predict", "factory_mixed", "factory_covariance"}:
        if task == "factory_covariance":
            worlds = list(quality_worlds(d, 2))
            ex = sum(weight * x[0] for _, x, weight in worlds)
            ey = sum(weight * x[1] for _, x, weight in worlds)
            exy = sum(weight * x[0] * x[1] for _, x, weight in worlds)
            return exy - ex * ey
        evidence = (1,) if task != "factory_mixed" else (1,) * d["good"] + (0,) * d["bad"]
        extra = int(task == "factory_predict")
        relevant = [
            (source, word, weight)
            for source, word, weight in quality_worlds(d, len(evidence) + extra)
            if word[: len(evidence)] == evidence
        ]
        denominator = sum(weight for _, _, weight in relevant)
        numerator = sum(
            weight for source, word, weight in relevant if (word[-1] == 1 if extra else source == 0)
        )
        return numerator / denominator
    if task == "evidence_order":
        return sum(sum(word) == d["good"] for word in it.product((0, 1), repeat=d["good"] + d["bad"]))
    if task == "prior_balance":
        # Posterior odds = prior odds × likelihood ratio; require posterior odds 1.
        odds = F(d["b"]) / F(d["a"])
        return odds / (1 + odds)
    if task == "sample_exact_defects":
        samples = list(it.combinations(range(d["good"] + d["bad"]), d["draws"]))
        successful = sum(sum(i >= d["good"] for i in sample) == d["defects"] for sample in samples)
        return F(successful, len(samples))
    if task == "stop_on_failure":
        total = F()
        for word in it.product((0, 1), repeat=d["limit"]):
            weight = F(1)
            for good in word:
                weight *= F(d["p"]) if good else 1 - F(d["p"])
            performed = word.index(0) + 1 if 0 in word else len(word)
            total += performed * weight
        return total
    if task == "conditional_failures":
        selected, both = F(), F()
        for x, y in it.product((0, 1), repeat=2):
            weight = (F(d["a"]) if x else 1 - F(d["a"])) * (F(d["b"]) if y else 1 - F(d["b"]))
            if x or y:
                selected += weight
                if x and y:
                    both += weight
        return both / selected
    if task == "positive_precision":
        population = [True] * d["detected"] + [False] * d["false"]
        return sum((F(int(x), len(population)) for x in population), F())
    if task == "fleet_range":
        # Exact capacity envelope: each lost tankful is burned at current fleet rate.
        fuel, distance = F(d["capacity"] * d["n"]), F()
        for moving in range(d["n"], 0, -1):
            lower_fuel = (moving - 1) * d["capacity"]
            interval = (fuel - lower_fuel) / moving
            distance += interval
            fuel -= moving * interval
            assert fuel == lower_fuel
        return distance
    if task == "fleet_abandon":
        fuel = sum(d["capacity"] - d["distance"] for _ in range(d["n"]))
        return next(k for k in range(d["n"] + 1) if k * d["capacity"] >= fuel)
    if task == "fleet_transfer":
        free = d["capacity"] - d["b"]
        moved = d["a"] if d["a"] <= free else free
        return F(d["b"] + moved, d["rate"])
    if task in {"graph_meeting", "meeting_tiebreak"}:
        dist = shortest_paths(d)
        scores = [(sum(dist[p][v] for p in d["people"]), v) for v in range(d["n"])]
        return min(scores)[0 if task == "graph_meeting" else 1]
    if task == "meeting_radius":
        # For integer input endpoints a minimax optimum is on the half-unit grid.
        scores = [
            max(abs(F(t, 2) - x) for x in d["positions"])
            for t in range(2 * min(d["positions"]), 2 * max(d["positions"]) + 1)
        ]
        return min(scores)
    if task == "reachable_meetings":
        components = []
        for source in d["people"]:
            reached, todo = {source}, deque([source])
            while todo:
                current = todo.popleft()
                for a, b, _ in d["edges"]:
                    neighbor = b if a == current else a if b == current else None
                    if neighbor is not None and neighbor not in reached:
                        reached.add(neighbor)
                        todo.append(neighbor)
            components.append(reached)
        return len(set.intersection(*components))
    if task == "shortcut_savings":
        old = {d["ab"] + d["bc"], d["ac"]}
        new = old | {d["new"]}
        return sorted(old)[0] - sorted(new)[0]
    if task == "cluster_mean":
        # Discrete differences of SSE around the candidate verify the minimizer.
        n = len(d["points"])
        candidates = [F(k, n) for k in range(n * min(d["points"]), n * max(d["points"]) + 1)]
        return min(candidates, key=lambda c: sum((c - x) ** 2 for x in d["points"]))
    if task == "cluster_sse":
        c = F(d["center"])
        # Expanded second-moment identity, independent of per-point squaring.
        return sum(x * x for x in d["points"]) - 2 * c * sum(d["points"]) + len(d["points"]) * c * c
    if task == "nearest_tie":
        return squared_assignment(d["x"], d["centers"])
    if task == "empty_cluster":
        members = [x for x in d["points"] if squared_assignment(x, d["centers"]) == d["index"]]
        return sum((F(x, len(members)) for x in members), F()) if members else F(d["centers"][d["index"]])
    if task == "merge_cost":
        groups = [d["left"], d["right"]]

        def energy(points):
            center = F(sum(points), len(points))
            return sum((x - center) ** 2 for x in points)

        return energy(d["left"] + d["right"]) - sum(energy(g) for g in groups)
    if task == "reassign_count":
        old = [squared_assignment(x, d["old"]) for x in d["points"]]
        new = [squared_assignment(x, d["new"]) for x in d["points"]]
        return len([i for i in range(len(old)) if old[i] != new[i]])
    if task == "sse_scaling":
        # A concrete witness realizes integer SSE as unit residuals.
        points = [F(1)] * d["sse"]
        center = F(d["shift"])
        transformed = [F(d["scale"]) * x + center for x in points]
        return sum((x - center) ** 2 for x in transformed)
    if task == "unseen_focus":
        return len(set(range(d["n"])) - set(d["seen"]))
    if task == "focus_plateau":
        for index, value in enumerate(d["values"]):
            if all(value >= other for other in d["values"]):
                return index
        raise AssertionError("Nonempty focus list required")
    if task == "noise_possible_max":
        possible = set()
        for values in it.product(*(range(lo, hi + 1) for lo, hi in d["intervals"])):
            for index in range(len(values)):
                if all(values[index] >= x for x in values):
                    possible.add(index)
        return len(possible)
    if task == "focus_travel":
        position, cost = d["start"], 0
        for target in [*d["order"], d["finish"]]:
            while position != target:
                position += 1 if target > position else -1
                cost += 1
        return cost
    if task == "settling_cost":
        position, elapsed = d["start"], 0
        for target in d["order"]:
            if target != position:
                elapsed += d["settle"]
                position = target
            elapsed += d["measure"]
        return elapsed
    if task == "lion_counts":
        eaten = [False]
        for _ in range(d["limit"]):
            eaten.append(not eaten[-1])
        return sum(eaten[1:])
    if task == "calendar_age":
        born, today = date_parts(d["born"]), date_parts(d["today"])
        anniversaries = [(year, born[1], born[2]) for year in range(born[0] + 1, today[0] + 1)]
        return sum(birthday <= today for birthday in anniversaries)
    if task == "calendar_days":
        current, end, elapsed = date_parts(d["start"]), date_parts(d["end"]), 0
        while current != end:
            current = next_day(current)
            elapsed += 1
        return elapsed
    if task == "freefall_height":
        # Constant acceleration: exact trapezoidal integral of linear velocity.
        t, g = F(d["time"]), F(d["g"])
        half = t / 2
        return half * (0 + g * half) / 2 + half * (g * half + g * t) / 2
    if task == "impact_sound":
        total = F(d["fall"])
        for _ in range(d["height"]):
            total += F(1, d["sound"])
        return total
    if task == "height_uncertainty":
        # Increment in height = average velocity over the additional interval × duration.
        lo, hi, g = F(d["low"]), F(d["high"]), F(d["g"])
        return (g * lo + g * hi) * (hi - lo) / 2
    if task == "fuel_units":
        metres_per_litre = F(d["unit"], d["rate"])
        return sum((metres_per_litre for _ in range(d["fuel"])), F())
    if task == "midpoint_pair_count":
        return sum(
            all(F(x + y, 2).denominator == 1 for x, y in zip(a, b, strict=True))
            for a, b in it.combinations(d["points"], 2)
        )
    if task == "parity_group_guarantee":
        signatures = list(it.product((0, 1), repeat=d["dimension"]))
        # Explicit avoiding construction; one more exhausts all bins' safe capacity.
        avoiding = [(signature, copy) for signature in signatures for copy in range(d["group"] - 1)]
        return len(avoiding) + 1
    if task == "midpoint_free_subset":
        valid = []
        for k in range(len(d["points"]) + 1):
            for chosen in it.combinations(d["points"], k):
                if all(
                    any((x + y) % 2 for x, y in zip(a, b, strict=True)) for a, b in it.combinations(chosen, 2)
                ):
                    valid.append(k)
        return max(valid)
    if task in {"knowledge_unique", "public_ignorance", "knows_other_ignorance"}:
        count = 0
        for actual in d["worlds"]:
            a_view = [world for world in d["worlds"] if world[0] == actual[0]]
            if task == "knowledge_unique":
                condition = len(a_view) == 1
            elif task == "public_ignorance":
                condition = len(a_view) != 1
            else:
                condition = all(
                    len([other for other in d["worlds"] if other[1] == world[1]]) > 1 for world in a_view
                )
            count += condition
        return count
    if task == "hat_worlds":
        return sum(
            word.count(0) <= d["white"] and word.count(1) <= d["black"]
            for word in it.product((0, 1), repeat=d["people"])
        )
    if task == "implication_counterexamples":
        return 2 ** d["n"] - len(list(truth_models(d)))
    if task == "forced_true":
        models = list(truth_models(d))
        assert models
        return len(set.intersection(*models))
    if task == "quantified_batches":
        accepted = 0
        for batch in d["batches"]:
            if batch and min(batch) >= d["low"] and max(batch) >= d["high"]:
                accepted += 1
        return accepted
    if task == "measurement_intersection":
        possible = set(range(d["intervals"][0][0], d["intervals"][0][1] + 1))
        for lo, hi in d["intervals"][1:]:
            possible &= set(range(lo, hi + 1))
        return len(possible)
    if task == "sum_uncertainty":
        totals = [sum(values) for values in it.product(*(range(lo, hi + 1) for lo, hi in d["intervals"]))]
        return max(totals) - min(totals)
    if task == "common_bias":
        # Many arbitrary shared biases yield one invariant difference.
        differences = {(d["x"] - bias) - (d["y"] - bias) for bias in range(-9, 10)}
        assert len(differences) == 1
        return differences.pop()
    if task == "minimax_experiment":
        return min(max(sum(other == outcome for other in test) for outcome in test) for test in d["tests"])
    if task == "expected_survivors":
        return sum((F(sum(y == x for y in d["outcomes"]), len(d["outcomes"])) for x in d["outcomes"]), F())
    if task == "code_distance":
        # Interpret strings as integers, then count bit flips by repeated division.
        distances = []
        for a, b in it.combinations(d["codes"], 2):
            difference, count = int(a, 2) ^ int(b, 2), 0
            while difference:
                difference, bit = divmod(difference, 2)
                count += bit
            distances.append(count)
        return min(distances)
    if task == "erased_observations":
        # Expand erased positions into all complete observations, then intersect.
        complete = {
            "".join(bits) for bits in it.product(*[("0", "1") if x == "x" else (x,) for x in d["observed"]])
        }
        return len(complete.intersection(d["codes"]))
    if task == "joint_information":
        classes = []
        for i in range(len(d["a"])):
            matching = {j for j in range(len(d["a"])) if d["a"][j] == d["a"][i] and d["b"][j] == d["b"][i]}
            if matching not in classes:
                classes.append(matching)
        return len(classes)
    if task == "capacity_slack":
        events = {}
        for start, end, demand in d["jobs"]:
            events[start] = events.get(start, 0) + demand
            events[end] = events.get(end, 0) - demand
        load, slack = 0, d["capacity"]
        for time in sorted(events):
            load += events[time]
            slack = min(slack, d["capacity"] - load)
        return slack
    if task == "deadline_capacity":
        # Explicitly assign unit jobs to available worker/time slots.
        deadlines = sorted(d["deadlines"])
        if not deadlines:
            return 0
        for workers in range(1, len(deadlines) + 1):
            free = [(slot, worker) for slot in range(1, max(deadlines) + 1) for worker in range(workers)]
            feasible = True
            for deadline in deadlines:
                available = next((x for x in free if x[0] <= deadline), None)
                if available is None:
                    feasible = False
                    break
                free.remove(available)
            if feasible:
                return workers
        raise AssertionError("Positive deadlines should admit a schedule")
    if task == "preemptive_work":
        # Exhaust small integer-slot schedules, with at most one worker/job/slot.
        work = tuple(d["work"])

        @lru_cache(None)
        def feasible(remaining, time, workers):
            if not any(remaining):
                return True
            if time == 0:
                return False
            active = [i for i, value in enumerate(remaining) if value]
            for selected in it.combinations(active, min(workers, len(active))):
                nxt = tuple(value - int(i in selected) for i, value in enumerate(remaining))
                if feasible(nxt, time - 1, workers):
                    return True
            return False

        return next(workers for workers in range(len(work) + 1) if feasible(work, d["deadline"], workers))
    if task == "route_deadlines":
        position, time, on_time = d["start"], 0, 0
        for dest, deadline in d["requests"]:
            time += abs(dest - position)
            position = dest
            on_time += time <= deadline
        return on_time
    if task == "order_implications":
        # Enumerate every total order compatible with the partial observations.
        orders = [
            order
            for order in it.permutations(range(d["n"]))
            if all(order.index(a) < order.index(b) for a, b in d["faster"])
        ]
        assert orders
        return sum(
            all(order.index(a) < order.index(b) for order in orders)
            for a in range(d["n"])
            for b in range(d["n"])
            if a != b
        )
    raise AssertionError(f"Missing independent oracle: {task}")


@pytest.mark.parametrize("case", CHECKS, ids=lambda case: case["key"])
def test_each_variant_against_input_derived_independent_oracle(case):
    actual = BY_KEY[case["key"]]
    result = str(F(oracle(case["task"], case["inputs"])))
    assert result == case["expected"]
    assert [choice["en"] for choice in actual["choices"]] == case["options"]
    for language in ("he", "en"):
        values = [choice[language] for choice in actual["choices"]]
        assert len(values) == len(set(values)) == 4
        assert values[actual["correct"]] == result
        assert sum(value == result for value in values) == 1
    assert actual["status"] == "draft"
    assert case["professional_review"] == "pending"


def test_exact_counts_ids_variants_and_concise_bilingual_contract():
    assert len(CARDS) == 70
    assert len(ROWS) == len(CHECKS) == len(BY_KEY) == 350
    assert {card["id"] for card in CARDS} == {f"quick-sw-{i}" for i in range(251, 321)}
    assert len({case["task"] for case in CHECKS}) == 70
    for card in CARDS:
        related = [row for row in ROWS if row["source_key"] == card["id"]]
        audits = [case for case in CHECKS if case["key"].rsplit("-v", 1)[0] == card["id"]]
        assert {row["variant"] for row in related} == {1, 2, 3, 4, 5}
        assert len({json.dumps(case["inputs"], sort_keys=True) for case in audits}) == 5
        assert len({row["prompt"]["en"] for row in related}) == 5
        assert len({(case["difficulty"], case["difficulty_rationale"]) for case in audits}) == 1
        assert len({case["expected"] for case in audits}) >= 2
        assert card["prompt"] == related[0]["prompt"]
        assert card["topic"] == "reasoning"
        assert "difficulty" not in card
        for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
            for language in ("he", "en"):
                value = card[field][language]
                assert value and len(value.split()) <= limit, (card["id"], field, language)
                assert "\ufffd" not in value
                assert not re.search(r"\{[a-zA-Z_]+\}", value)
                assert bool(re.search(r"[\u0590-\u05ff]", value)) == (language == "he")
    for row in ROWS:
        for language in ("he", "en"):
            assert len(row["prompt"][language].split()) <= 50
            assert len(row["explanation"][language].split()) <= 65
            assert bool(re.search(r"[\u0590-\u05ff]", row["prompt"][language])) == (language == "he")
        assert re.findall(r"\d+", row["prompt"]["en"]) == re.findall(r"\d+", row["prompt"]["he"]), row["key"]
        assert "difficulty" not in row


def test_real_provenance_private_difficulty_and_no_old_identity_or_text_reuse():
    editorial = json.loads((ROOT / "backend/seeds/preparation_editorial.json").read_bytes())
    interviews = {
        row["id"]
        for row in json.loads((ROOT / "interview_preparation/questions.json").read_bytes())["questions"]
    }
    examples = {
        row["id"] for row in json.loads((ROOT / "example_question/questions.json").read_bytes())["questions"]
    }
    localized = set()
    for path in (ROOT / "backend/seeds/preparation_localization").glob("*.json"):
        localized.update(json.loads(path.read_bytes()))
    old_cards = []
    for path in CONTENT.glob("fundamentals-*.json"):
        if "700" in path.name or "revisions" in path.name:
            continue
        data = json.loads(path.read_bytes())
        if isinstance(data, list):
            old_cards.extend(data)
    old_ids = {card["id"] for card in old_cards}
    old_prompts = {card["prompt"]["en"] for card in old_cards}
    old_titles = {card["title"]["en"] for card in old_cards}
    assert len(old_cards) == 500
    for card in CARDS:
        assert card["id"] not in old_ids
        assert card["title"]["en"] not in old_titles
        assert card["prompt"]["en"] not in old_prompts
        assert card["interviewIds"]
        for reference in card["interviewIds"]:
            assert reference in interviews | examples
            if reference.startswith("PREP-"):
                assert reference in editorial and reference in localized
    for case in CHECKS:
        assert isinstance(case["difficulty"], int) and 1 <= case["difficulty"] <= 10
        assert case["difficulty_rationale"]
        assert case["source_difficulty"] == case["difficulty"]
        assert case["source_difficulty_rationale"] == case["difficulty_rationale"]
        assert case["authorship"].startswith("AI-assisted")
        assert "not a reported interview variant" in case["source_relation"]


def test_known_boundary_counterexamples():
    assert oracle("coin_min", {"coins": [2, 3, 6], "target": 7}) == -1
    assert oracle("coin_ways", {"coins": [2, 2, 2], "target": 4}) == 3
    assert oracle("noise_possible_max", {"intervals": [[2, 2], [1, 2]]}) == 2
    assert oracle("forced_true", {"n": 3, "rules": [[0, 1], [1, 2]], "known": [[2, 1]]}) == 1
    assert oracle("preemptive_work", {"work": [3, 3, 3], "deadline": 5}) == 2
    assert oracle("capacity_slack", {"capacity": 5, "jobs": [[0, 1, 5], [1, 2, 5]]}) == 0
    assert oracle("order_implications", {"n": 4, "faster": [[0, 1], [2, 3]]}) == 2


def test_generation_is_reproducible_without_writing():
    path = ROOT / "backend/scripts/quiz_authoring/reasoning_700.py"
    spec = importlib.util.spec_from_file_location("reasoning700_authoring", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_bundle() == (CARDS, ROWS, CHECKS)
    assert module.build() == (ROWS, CHECKS)


def test_every_variant_passes_publication_text_validation():
    path = ROOT / "backend/scripts/quiz_authoring/assemble.py"
    spec = importlib.util.spec_from_file_location("reasoning700_text_validation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for row in ROWS:
        for language in ("he", "en"):
            for field in ("prompt", "explanation"):
                assert not module.text_issues(row[field][language], language, field), (
                    row["key"],
                    field,
                    language,
                )
            for choice in row["choices"]:
                assert not module.text_issues(choice[language], language, "choice"), (row["key"], language)
