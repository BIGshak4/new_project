"""Independent finite worlds and exact arithmetic for 52 cards and 260 MCQs.

These inspect actual authored answers as well as answer indices. No AI judgement
or physical experiment is claimed by the mathematical models.
"""

from __future__ import annotations

import ast
import importlib.util
import itertools
import json
import math
import re
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
BATCH = ROOT / "backend/seeds/duel_quiz_batches"
CARDS = json.loads((CONTENT / "fundamentals-reasoning-400.json").read_bytes())
ROWS = json.loads((BATCH / "reasoning_400.json").read_bytes())
CHECKS = json.loads((BATCH / "reasoning_400.checks.json").read_bytes())


def assignments(edges):
    """Backtracking oracle; not the producer's product/filter implementation."""

    def visit(i, used, chosen):
        if i == len(edges):
            yield tuple(chosen)
            return
        for item in edges[i]:
            if item not in used:
                yield from visit(i + 1, used | {item}, [*chosen, item])

    return list(visit(0, set(), []))


def turn(a, b, c):
    return (a[0] - c[0]) * (b[1] - c[1]) - (a[1] - c[1]) * (b[0] - c[0])


def polygon_oracle(points):
    """Boundary simplicity by rational line parameters,then support half-planes."""
    n = len(points)
    if all(turn(points[0], points[1], point) == 0 for point in points):
        return "degenerate"
    for i, j in itertools.combinations(range(n), 2):
        if (i - j) % n in (1, n - 1):
            continue
        a, b, c, d = points[i], points[(i + 1) % n], points[j], points[(j + 1) % n]
        rx, ry, sx, sy = b[0] - a[0], b[1] - a[1], d[0] - c[0], d[1] - c[1]
        det = rx * sy - ry * sx
        if det:
            t = F((c[0] - a[0]) * sy - (c[1] - a[1]) * sx, det)
            u = F((c[0] - a[0]) * ry - (c[1] - a[1]) * rx, det)
            if 0 < t < 1 and 0 < u < 1:
                return "crossing"
    for i in range(n):
        signs = {
            int(math.copysign(1, t)) for point in points if (t := turn(points[i], points[(i + 1) % n], point))
        }
        if len(signs) > 1:
            return "concave"
    return (
        "weak"
        if any(turn(points[i], points[(i + 1) % n], points[(i + 2) % n]) == 0 for i in range(n))
        else "strict"
    )


def public_announcement_round(red):
    n = red + 1
    worlds = [w for w in itertools.product((0, 1), repeat=n) if any(w)]
    actual = (1,) * red + (0,)
    for round_number in range(1, n + 1):
        declarations = {}
        for world in worlds:
            signals = []
            for i in range(n):
                possibilities = {w[i] for w in worlds if all(w[j] == world[j] for j in range(n) if i != j)}
                signals.append(possibilities == {1})
            declarations[world] = tuple(signals)
        heard = declarations[actual]
        if any(heard):
            return round_number
        worlds = [w for w in worlds if declarations[w] == heard]
    raise AssertionError("No first announcement in the finite model")


def graphical(degrees):
    """Havel-Hakimi, independent of producer's edge enumeration."""
    remaining = list(degrees)
    while True:
        remaining.sort(reverse=True)
        if not remaining or remaining[0] == 0:
            return all(d == 0 for d in remaining)
        d = remaining.pop(0)
        if d < 0 or d > len(remaining):
            return False
        for i in range(d):
            remaining[i] -= 1
        if any(x < 0 for x in remaining):
            return False


def independent_value(number, d):
    if number == 126:
        return min(sum(a[i] != x for i, x in enumerate(d["old"])) for a in assignments(d["edges"]))
    if number == 127:
        # Maximum matching via explicit unmatched sentinel; deficiency equals unavoidable unmatched count.
        edges = [x + [-i - 1] for i, x in enumerate(d["edges"])]
        return min(sum(x < 0 for x in a) for a in assignments(edges))
    if number == 128:
        events = [(t, sign * w) for a, b, w in d["jobs"] for t, sign in ((a, 1), (b, -1))]
        changes = Counter()
        for t, w in events:
            changes[t] += w
        running = peak = 0
        for t in sorted(changes):
            running += changes[t]
            peak = max(peak, running)
        return peak
    if number == 129:
        uncovered = []
        for skill in range(2):
            slots = [skill] * d["need"][skill]
            available = [skill] * d["have"][skill]
            for slot in slots:
                if slot in available:
                    available.remove(slot)
                else:
                    uncovered.append(slot)
        return len(uncovered)
    if number == 130:
        possibilities = set(d["allowed"])
        if not possibilities:
            return 3
        if len(possibilities) > 1:
            return 0
        return {500: 1, 400: 2}[possibilities.pop()]
    if number == 131:
        targets = {d["low"] - 1, d["low"], d["high"], d["high"] + 1}
        assert len(targets) >= 3
        return 0
    if number == 132:
        lo, hi = d["reading"] - d["error"], d["reading"] + d["error"]
        passing = {x <= d["limit"] for x in range(lo, hi + 1)}
        return 0 if passing == {True} else 1 if passing == {False} else 2
    if number == 133:
        return len([i for i in range(len(d["expected"])) if d["expected"][i] ^ d["observed"][i]])
    if number == 134:
        seen = [any(r in test for test in d["covers"]) for r in range(d["total"])]
        return seen.count(False)
    if number == 135:
        return sum(len(set(pair)) != 1 for pair in d["pairs"])
    if number == 136:
        # Final original-red amount in A is its volume minus final blue volume.
        original_red_left = d["a"] - d["q"]
        return d["a"] - original_red_left
    if number == 137:
        fa, fb = F(d["q"], d["a"]), F(d["q"], d["b"])
        return 3 if fa == fb == 0 else 0 if fa > fb else 1 if fb > fa else 2
    if number == 138:
        allowed_return_time = F(2, d["g"]) - F(1, d["u"])
        return 0 if allowed_return_time > 0 else 1 if allowed_return_time == 0 else 2
    if number == 139:
        return 1 / (F(2, d["g"]) - F(1, d["u"]))
    if number == 140:
        # Solve net heat transfer to zero rather than call the weighted-average formula.
        energy = d["cc"] * d["hot"] + d["cm"] * d["cold"]
        temperature = F(energy, d["cc"] + d["cm"])
        assert d["cc"] * (temperature - d["hot"]) + d["cm"] * (temperature - d["cold"]) == 0
        return temperature
    if number == 141:
        if d["b"] is None:
            return 3
        early = F(90 * d["cc"] + 10 * d["cm"], d["cc"] + d["cm"]) - F(d["b"])
        late = F((90 - d["a"]) * d["cc"] + 10 * d["cm"], d["cc"] + d["cm"])
        return 0 if early > late else 1 if late > early else 2
    if number == 142:
        time, height = F(0), F(0)
        while True:
            if height + d["up"] >= d["height"]:
                return time + (d["height"] - height) / d["up"]
            height += d["up"] - d["down"]
            time += 2
    if number == 143:
        meeting = [
            t for t in range(d["right"] - d["left"] + 1) if d["left"] + d["a"] * t == d["right"] - d["b"] * t
        ]
        return meeting[0] if meeting else 3
    if number == 144:
        if d["rule"] in (None, "decreasing"):
            # Two concrete extensions fit every supplied condition and differ at the next term.
            assert d["prefix"] + [d["prefix"][-1] - 1] != d["prefix"] + [d["prefix"][-1] - 2]
            return 0
        step = d["prefix"][-2] - d["prefix"][-1]
        next_step = step + 1 if d["rule"] == "growing" else 2
        return {91: 1, 93: 2, 94: 3}[d["prefix"][-1] - next_step]
    if number == 145:
        same_sum = all(x == d["sums"][0] for x in d["sums"])
        same_area = all(x == d["areas"][0] for x in d["areas"])
        return {(True, False): 0, (False, True): 1, (True, True): 2, (False, False): 3}[(same_sum, same_area)]
    if number == 146:
        failures = []
        for index, labels in enumerate(d["candidates"]):
            membership = [i in labels for i in range(d["count"])]
            changes = sum(a != b for a, b in zip(membership, membership[1:] + membership[:1], strict=True))
            if changes > 2:
                failures.append(index)
        assert len(failures) == 1
        return failures[0]
    if number == 147:
        r, x = d["radius"], d["distance"]
        legal = x - r >= r
        disjoint = -x + r <= x - r
        return {(True, True): 0, (False, True): 1, (False, False): 2, (True, False): 3}[(legal, disjoint)]
    if number == 148:
        remaining, count = d["table"] ** 2, 0
        while remaining >= d["coin"] ** 2:
            remaining -= d["coin"] ** 2
            count += 1
        return count
    if number == 149:
        if d["rho"] is None:
            return 3
        rho, water = F(d["rho"]), F(d["water"])
        before = F(10, water) + rho / water
        after = F(10, water) + min(F(1), rho / water)
        return 0 if after < before else 1 if after == before else 2
    if number == 150:
        return sum(F(1, 2 * d["a"]) for ball in range(d["a"]) if ball == 0)
    if number == 151:
        a, b = d["size"], d["total"] - d["size"]
        if a == 0 or b == 0:
            return 3
        before = F(1, 2 * b)  # A all white,B has exactly one red.
        after = F(1, 2 * a)
        return 0 if after > before else 1 if after == before else 2
    if number == 152:
        return len(set(itertools.product(range(d["coins"]), d["directions"])))
    if number == 153:
        for bits in range(1, 10):
            nonzero = [x for x in itertools.product((0, 1), repeat=bits) if any(x)]
            if len(nonzero) >= d["bottles"]:
                return bits
    if number == 154:
        width = (d["bottles"] - 1).bit_length()
        observable = set()
        for poison in range(d["bottles"]):
            observable.add(
                tuple(
                    ((poison >> bit) & 1) if d["observe"] >= d["start"] + d["delay"] else 0
                    for bit in range(width)
                )
            )
        return len(observable)
    if number == 155:
        n = d["people"]
        blocks = [3] * (n // 3)
        blocks[-1] += n % 3
        assert sum(blocks) == n and all(size >= 3 for size in blocks)
        return sum(size - 1 for size in blocks)
    if number == 156:
        n = d["people"]
        correct_counts = []
        for hats in itertools.product((0, 1), repeat=n):
            answers = [sum(hats[1:]) % 2]
            for i in range(1, n):
                answers.append((answers[0] + sum(answers[1:]) + sum(hats[i + 1 :])) % 2)
            correct_counts.append(sum(a == h for a, h in zip(answers, hats, strict=True)))
        # The first speaker sees identical front hats with either own hat; cannot guarantee all n.
        assert hats[1:] == ((1 - hats[0]), *hats[1:])[1:]
        return min(correct_counts)
    if number == 157:
        candidates = [hat for hat in range(3) if (sum(d["known"]) + hat) % 3 == d["checksum"]]
        assert len(candidates) == 1
        return candidates[0]
    if number == 158:
        counts = []
        n = d["colors"]
        for hats in itertools.product(range(n), repeat=n):
            guesses = [(d["offsets"][i] - sum(hats[:i]) - sum(hats[i + 1 :])) % n for i in range(n)]
            counts.append(sum(g == h for g, h in zip(guesses, hats, strict=True)))
        return min(counts)
    if number == 159:

        def peel(n, degree):
            if degree == 0:
                return 2 * n - 2
            if degree == 2 * n - 2:
                return 0
            return 1 + peel(n - 1, degree - 1)

        return peel(d["couples"], d["degree"])
    if number == 160:
        return public_announcement_round(d["red"])
    if number == 161:
        itinerary = []
        for load in range(d["loads"]):
            itinerary.append("forward")
            if load + 1 < d["loads"]:
                itinerary.append("back")
        return len(itinerary)
    if number == 162:
        stock, capacity = d["stock"], d["capacity"]
        k = next(k for k in range(1, stock + 1) if k * capacity >= stock)
        target = (k - 1) * capacity
        consumption = sum(1 for _ in range(k)) + sum(1 for _ in range(k - 1))
        return F(stock - target, consumption)
    if number == 163:
        return {"strict": 0, "weak": 0, "concave": 1, "crossing": 2, "degenerate": 3}[
            polygon_oracle(d["points"])
        ]
    if number == 164:
        return {"strict": 0, "weak": 1, "concave": 2, "degenerate": 3}[polygon_oracle(d["points"])]
    if number == 165:
        mapping = dict(
            zip(range(d["count"]), [*range(d["offset"], d["count"]), *range(d["offset"])], strict=True)
        )
        return mapping[d["survivor"]]
    if number == 166:
        equivalent = any(all(d["a"][i] == d["b"][(i + shift) % 4] for i in range(4)) for shift in range(4))
        return 0 if equivalent else 1 if sorted(d["a"]) != sorted(d["b"]) else 2
    if number == 167:
        possibles = {0, 1}
        for bush in d["schedule"]:
            possibles = {1 - x for x in possibles if x != bush}
        return len(possibles)
    if number == 168:
        a, b, c, e = (d[k] for k in ("a", "b", "c", "d"))
        first = [max(a, b), a, max(c, e), b, max(a, b)]
        second = [max(a, e), a, max(a, c), a, max(a, b)]
        return min(sum(first), sum(second))
    if number == 169:
        side = {"torch": "left", **{x: "left" for x in "ABC"}}
        for i, (people, direction) in enumerate(d["schedule"], 1):
            origin, destination = ("left", "right") if direction == 1 else ("right", "left")
            if any(side[x] != origin for x in ["torch", *people]):
                return i
            side.update({x: destination for x in ["torch", *people]})
        return 0
    if number == 170:
        outcomes = [any(code & 2**bit for code in (d["x"], d["y"])) for bit in range(4)]
        return sum(2**bit for bit, positive in enumerate(outcomes) if positive)
    if number == 171:
        p, hit, miss = (F(d[k]) for k in ("prob", "hit", "miss"))
        paths = [(p * hit, 1), (p * (1 - hit), 0), ((1 - p) * miss, 1), ((1 - p) * (1 - miss), 0)]
        attempt = sum(probability * won for probability, won in paths)
        return 0 if attempt > miss else 1 if attempt < miss else 2
    if number == 172:
        partitions = [{reading for reading in predictions} for predictions in d["predictions"]]
        assert sum(len(part) == 2 for part in partitions) == 1
        return next(i + 1 for i, part in enumerate(partitions) if len(part) == 2)
    if number == 173:
        joint_a = sum(F(1, 2 * (d["ar"] + d["aw"])) for _ in range(d["ar"]))
        joint_b = sum(F(1, 2 * (d["br"] + d["bw"])) for _ in range(d["br"]))
        return joint_a / (joint_a + joint_b)
    if number == 174:
        last = [k for k in range(4) if graphical([*d["prefix"], k])]
        if not last:
            return 3
        assert all((sum(d["prefix"]) + k) % 2 == 0 for k in last)
        return last[0] % 2 if len({k % 2 for k in last}) == 1 else 2
    if number == 175:
        buckets = Counter()
        for light in range(d["total"]):
            weights = [1 if i == light else 2 for i in range(d["total"])]
            difference = sum(weights[: d["pan"]]) - sum(weights[d["pan"] : 2 * d["pan"]])
            buckets[(difference > 0) - (difference < 0)] += 1
        return max(buckets.values())
    if number == 176:
        snapshots = {}
        log = [d["initial"]]
        for event in d["events"]:
            if event.startswith("R"):
                snapshots[event[-1]] = log[-1]
            else:
                log.append(snapshots[event[-1]] + 1)
        return log[-1]
    if number == 177:
        return max(
            floor
            for floor in range(1 + max(k for k, _ in d["outcomes"]))
            if all(k >= floor for k, weight in d["outcomes"] if weight > 0)
        )
    raise AssertionError(number)


@pytest.mark.parametrize("record", CHECKS, ids=lambda r: r["key"])
def test_all_260_cases_match_independent_oracles_and_actual_chosen_answer(record):
    number = int(record["key"].split("-")[2])
    actual = independent_value(number, record["inputs"])
    assert str(actual) == record["value"]
    row = next(q for q in ROWS if q["key"] == record["key"])
    assert row["choices"][row["correct"]] == record["expected"]
    for language in ("he", "en"):
        assert len({option[language] for option in row["choices"]}) == 4
        assert row["explanation"][language].strip()
    if number == 131:
        d = record["inputs"]
        required = {d["low"] - 1, d["low"], d["high"], d["high"] + 1}
        valid = [
            i for i, option in enumerate(row["choices"]) if required <= set(ast.literal_eval(option["en"]))
        ]
        assert valid == [row["correct"]]


@pytest.mark.parametrize("card", CARDS, ids=lambda c: c["id"])
def test_each_short_card_has_verified_case_and_complete_bounded_text(card):
    evidence = next(c for c in CHECKS if c["key"] == card["id"] + "-v1")
    assert str(independent_value(int(card["id"].split("-")[-1]), evidence["inputs"])) == evidence["value"]
    for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
        assert set(card[field]) == {"he", "en"}
        for language in ("he", "en"):
            text = card[field][language]
            assert text.strip() and len(text.split()) <= limit
            assert "\ufffd" not in text
            if language == "en":
                assert not re.search("[א-ת]", text)
        if field == "answer":
            for language in ("he", "en"):
                assert card[field][language].startswith(evidence["expected"][language] + ". ")


def test_producer_is_reproducible_and_preserves_existing_ids():
    spec = importlib.util.spec_from_file_location(
        "reasoning400", ROOT / "backend/scripts/quiz_authoring/reasoning_400.py"
    )
    author = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(author)
    assert author.build_bundle() == (CARDS, ROWS, CHECKS)
    assert len(CARDS) == 52 and [c["id"] for c in CARDS] == [f"quick-sw-{n}" for n in range(126, 178)]
    assert len(ROWS) == len(CHECKS) == 260
    assert Counter(row["source_key"] for row in ROWS) == {card["id"]: 5 for card in CARDS}
    assert all(row["status"] == "draft" for row in ROWS)
    old = [
        c
        for path in CONTENT.glob("fundamentals-*.json")
        if "400" not in path.name and "revisions" not in path.name
        for c in json.loads(path.read_bytes())
    ]
    known_interviews = {
        q["id"] for q in json.loads((ROOT / "interview_preparation/questions.json").read_bytes())["questions"]
    }
    for card in CARDS:
        assert card["topic"] == "reasoning" and card["interviewIds"]
        assert set(card["interviewIds"]) <= known_interviews
        assert "company" not in card and "solution_review" not in card
        for language in ("he", "en"):
            for field in ("title", "prompt"):
                assert card[field][language] not in {c[field][language] for c in old}


def test_exchange_direction_holds_for_all_small_valid_red_white_compositions():
    for total in range(2, 13):
        for size in range(1, total):
            for red_a in range(size):
                for red_b in range(1, total - size + 1):
                    before = (F(red_a, size) + F(red_b, total - size)) / 2
                    after = (F(red_a + 1, size) + F(red_b - 1, total - size)) / 2
                    assert (after > before) == (size < total - size)
                    assert (after == before) == (size == total - size)
