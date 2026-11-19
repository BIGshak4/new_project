"""Recompute every new reasoning answer independently of the authoring shard."""

import importlib.util
import itertools
import json
import math
from collections import Counter, deque
from datetime import datetime, timedelta
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / "backend/seeds/duel_quiz_batches"
ROWS = json.loads((BATCH / "reasoning_800.json").read_bytes())
CHECKS = json.loads((BATCH / "reasoning_800.checks.json").read_bytes())
CARDS = json.loads((ROOT / "apps/web/src/content/fundamentals-reasoning-800.json").read_bytes())
CASES = list(zip(ROWS, CHECKS, strict=True))


def each_path(x, y):
    for rights in itertools.combinations(range(x + y), x):
        i = j = 0
        visited = {(i, j)}
        for step in range(x + y):
            if step in rights:
                i += 1
            else:
                j += 1
            visited.add((i, j))
        yield visited


def radix_digits(number, base):
    digits = []
    while number:
        number, digit = divmod(number, base)
        digits.append(digit)
    return digits


def oracle(task, d):
    if task == "copy_scale":
        # Try every canvas width in units of 1/c; require equal apparent widths.
        return next(w for q in range(1000) if (w := Fraction(q, d["c"])) * d["c"] == d["w"] * d["m"])
    if task == "traffic_delay":
        # Solve the distance equation in half-minute increments for these cases.
        return next(t / 2 for t in range(2 * d["t"] + 1) if (d["t"] - Fraction(t, 2)) * d["v"] == 60 * d["d"])
    if task == "hidden_share":
        # Identity permutations do not change the combined amount for any chosen share.
        items = range(d["a"] + d["b"])
        share = Fraction(d["goal"], d["a"])
        for positions in itertools.combinations(items, d["a"]):
            assert sum(share for _ in positions) == d["goal"]
        return share
    if task == "cooldown_return":
        prior = set(range(1, d["k"] + 1))
        return Fraction(1, len(set(range(d["n"])) - prior))
    if task == "cooldown_sequences":
        return sum(
            all(word[i] not in word[max(i - d["k"], 0) : i] for i in range(len(word)))
            for word in itertools.product(range(d["n"]), repeat=d["t"])
        )
    if task == "cooldown_cycle":
        sequence = list(range(1, d["n"] + 1))
        while len(sequence) < d["t"]:
            candidates = set(range(1, d["n"] + 1)) - set(sequence[-d["k"] :])
            assert len(candidates) == 1
            sequence.append(candidates.pop())
        return sequence[-1]
    if task == "service_sites":
        # Add pumps station by station until all clients can be served.
        sites = 0
        remaining = d["d"]
        while remaining > 0:
            for _ in range(d["p"]):
                remaining -= d["h"] * d["r"]
            sites += 1
        return sites
    if task == "station_bounds":
        return next(
            sites
            for sites in range(d["hi"] + 1)
            if all(
                sites * capacity >= demand for demand in (d["lo"], d["hi"]) for capacity in (d["a"], d["b"])
            )
        )
    if task == "weighing_label":
        return next(j for j in range(1, 100) if d["normal"] + j * d["delta"] == d["actual"])
    if task == "zero_sample":
        # Enumerate sorted distinct counts; any larger count can be compressed to a gap.
        n = d["n"]
        return min(sum(counts) for counts in itertools.combinations(range(n + 2), n))
    if task == "opening_byes":
        # The field after round one must be a power of 2. No duplicates or arbitrary byes.
        for byes in range(d["n"]):
            paired = d["n"] - byes
            if paired % 2 == 0 and (byes + paired // 2).bit_count() == 1:
                return byes
    if task == "survivor_rounds":
        field = list(range(d["n"]))
        for _ in range(d["r"]):
            field = field[::2]
        return len(field)
    if task == "factorial_jump":
        assert d["prev"] + 1 == d["n"]

        def zeros(n):
            decimal = str(math.factorial(n))
            return len(decimal) - len(decimal.rstrip("0"))

        return zeros(d["n"]) - zeros(d["prev"])
    if task == "factorial_radix":
        digits = radix_digits(math.factorial(d["n"]), d["base"])
        return next(i for i, glyph in enumerate(digits) if glyph != 0)
    if task == "power_ratio":
        p = d["a"].bit_length() - 1
        q = d["b"].bit_length() - 1
        assert 2**p == d["a"] and 2**q == d["b"]
        return Fraction(2) ** (d["i"] * p - d["j"] * q)
    if task == "lockstep_coverage":
        return len({start + i for start in (0, d["gap"]) for i in range(d["s"] + 1)})
    if task == "excursion_cost":
        trajectory = []
        for direction, leg in zip(itertools.cycle((1, -1)), d["legs"], strict=False):
            trajectory.extend([direction] * leg + [-direction] * leg)
            assert sum(trajectory) == 0
        return len(trajectory + [1] * d["last"])
    if task == "clock_interval":
        start = datetime.strptime(d["start"], "%H:%M:%S")
        end = datetime.strptime(d["end"], "%H:%M:%S")
        count = 0
        while start <= end:
            count += len(Counter(start.strftime("%H%M%S"))) <= 2
            start += timedelta(seconds=1)
        return count
    if task == "clock_minutes":
        allowed = set(str(d["a"]) + str(d["b"]))
        return sum(set(d["hour"] + f"{minute:02d}") <= allowed for minute in range(60))
    if task in ("checkpoint_paths", "obstacle_paths"):
        point = (d["a"], d["b"])
        return sum(((point in path) == (task == "checkpoint_paths")) for path in each_path(d["x"], d["y"]))
    if task == "grid_clashes":
        return sum(
            sum(green == red + delta for delta in (-2, -1, 1, 2)) for green in d["green"] for red in d["red"]
        )
    if task == "pyramid_pixels":
        rows, cols = list(range(d["h"])), list(range(d["w"]))
        counts = [len(rows) * len(cols)]
        for _ in range(d["levels"]):
            rows, cols = rows[::2], cols[::2]
            counts.append(len(rows) * len(cols))
        return sum(counts)
    if task == "drainage":
        # Grow the basin backward, one layer of uphill sites at a time.
        z = d["z"]
        basin = {d["sink"]}
        while True:
            expanded = basin.copy()
            for i in range(len(z)):
                neighbors = sorted((z[j], j) for j in (i - 1, i + 1) if j in range(len(z)))
                if neighbors and neighbors[0][0] < z[i] and neighbors[0][1] in basin:
                    expanded.add(i)
            if expanded == basin:
                return len(basin)
            basin = expanded
    if task == "josephus_rotate":
        circle = deque(range(1, d["n"] + 1))
        circle.rotate(1 - d["s"])
        while len(circle) > 1:
            circle.rotate(-1)
            circle.popleft()
        return circle[0]
    if task == "silence_worlds":
        return sum(sum(bits) > d["r"] for bits in itertools.product((0, 1), repeat=d["n"]))
    if task == "digit_chain":
        alphabet = set("".join(d["pairs"]))
        return sum(
            all(a + b in d["pairs"] for a, b in itertools.pairwise(word))
            for word in itertools.product(alphabet, repeat=d["n"])
        )
    if task in ("majority_error", "unanimous_error"):
        p = Fraction(d["p"])
        mass = Fraction()
        wrong = Fraction()
        for flips in itertools.product((0, 1), repeat=3):
            if task == "unanimous_error" and len(set(flips)) > 1:
                continue
            weight = math.prod(p if flip else 1 - p for flip in flips)
            mass += weight
            if sum(flips) >= 2:
                wrong += weight
        return wrong / mass
    if task == "repeat_coverage":
        # Construct a schedule by prioritizing channels with the most tests remaining.
        remaining = [d["r"]] * d["n"]
        rounds = 0
        while any(remaining):
            remaining.sort(reverse=True)
            for i in range(d["k"]):
                remaining[i] = max(remaining[i] - 1, 0)
            rounds += 1
        assert (rounds - 1) * d["k"] < d["r"] * d["n"]
        return rounds
    if task == "pyramid_indent":
        return sum((d["w"] - len(line)) // 2 for line in ("*" * k for k in range(1, d["w"] + 1, 2)))
    if task == "cube_layers":
        lower = [word for word in range(2 ** d["d"]) if word.bit_count() == d["k"]]
        upper = [word for word in range(2 ** d["d"]) if word.bit_count() == d["k"] + 1]
        return sum((a ^ b).bit_count() == 1 for a in lower for b in upper)
    if task == "expression_slots":
        return sum(
            sum(bool(s) for s in gaps) == d["groups"] - 1
            for gaps in itertools.product(("", "+", "-"), repeat=d["n"] - 1)
        )
    if task == "parking_prefix":
        return next(
            cars
            for cars in range(len(d["events"]) + 1)
            if all(cars + sum(d["events"][:k]) >= 0 for k in range(len(d["events"]) + 1))
        )
    if task == "sampling_overlap":
        first = set(range(0, d["hi"] + 1, d["a"]))
        second = set(range(0, d["hi"] + 1, d["b"]))
        return sum(i >= d["lo"] for i in first & second)
    raise AssertionError(task)


@pytest.mark.parametrize("row,check", CASES, ids=[row["key"] for row in ROWS])
def test_answers(row, check):
    expected = str(Fraction(oracle(check["task"], check["inputs"])))
    assert row["key"] == check["key"]
    assert expected == check["expected"]
    assert row["choices"][row["correct"]] == {"he": expected, "en": expected}
    assert len(set(check["options"])) == 4
    for lang in ("he", "en"):
        assert expected in row["explanation"][lang]


def test_rebuild_and_provenance():
    path = ROOT / "backend/scripts/quiz_authoring/reasoning_800.py"
    spec = importlib.util.spec_from_file_location("reasoning_800", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_bundle() == (CARDS, ROWS, CHECKS)
    assert [q["id"] for q in CARDS] == [f"quick-sw-{n}" for n in range(351, 386)]
    assert len(set(c["task"] for c in CHECKS)) == 35
    available = {
        q["assets"]["preparation_id"]
        for q in json.loads((ROOT / "backend/seeds/questions/preparation_bank.json").read_bytes())
    }
    for card in CARDS:
        assert card["interviewIds"] and set(card["interviewIds"]) <= available
        quizzes = [q for q in ROWS if q["source_key"] == card["id"]]
        assert [q["variant"] for q in quizzes] == [1, 2, 3, 4, 5]
        for lang in ("he", "en"):
            assert len({q["prompt"][lang] for q in quizzes}) == 5
