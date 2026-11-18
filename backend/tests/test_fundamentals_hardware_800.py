"""Replay the 50 circuit scenarios independently of the authored answer options."""

from __future__ import annotations

import importlib.util
import itertools
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARDS = ROOT / "backend/seeds/duel_quiz_batches"
CONTENT = ROOT / "apps/web/src/content"
CARDS = json.loads((CONTENT / "fundamentals-hardware-800.json").read_bytes())
QUIZ = json.loads((SHARDS / "hardware_800.json").read_bytes())
CHECKS = json.loads((SHARDS / "hardware_800.checks.json").read_bytes())


def antenna_and_mirror():
    def phase(distance):
        return distance * 360 / 12

    def distance(angle, spacing=6):
        return spacing * math.sin(math.radians(angle))

    def meter(degrees):
        return (degrees + 25) % 360

    def geometric(reading):
        return (reading - 25) % 360

    def mirror(reference, width):
        return reference * width / 2

    def branches(reference, widths):
        return sum(mirror(reference, w) for w in widths)

    yield 351, [phase(3), 180 / phase(1), phase(-2), phase(5) - phase(1), phase(15) % 360]
    yield (
        352,
        [
            round(distance(30)),
            round(math.degrees(math.asin(-3 / 6))),
            max(abs(distance(i)) for i in range(-90, 91)),
            distance(0),
            round(distance(30, 8)),
        ],
    )
    yield 353, [geometric(85), meter(350), geometric(10), meter(0), geometric(95) - geometric(75)]
    yield 354, [mirror(40, 6), 75 / mirror(1, 6), mirror(47, 6) - mirror(40, 6), mirror(1, 4), 5 * 2]
    boundary = 720 - 480
    yield 355, [boundary, 310 - boundary, boundary - 180, 800 - 480, 200 + 480]
    yield (
        356,
        [
            branches(20, [4, 6]),
            branches(20, [2, 4, 6]),
            mirror(20, 6) - mirror(20, 4),
            branches(20, [4, 6, 2]),
            150 / branches(1, [4, 6]),
        ],
    )


def bytes_and_votes():
    trace = [(1, 0, 126), (1, 1, 126), (1, 1, 0), (0, 1, 126), (1, 1, 126)]
    accepted = [(i, byte) for i, (v, r, byte) in enumerate(trace, 1) if v and r]
    matches = sum(byte == 126 for _, byte in accepted)
    yield (
        357,
        [
            matches,
            len(accepted),
            next(i for i, byte in accepted if byte != 126),
            sum(byte == 126 and not (v and r) for v, r, byte in trace),
            matches + 1,
        ],
    )
    count = 6
    wrapped = []
    for hit in [1, 1, 0, 1]:
        count += hit
        wrapped.append(count % 8)
    yield 358, [wrapped[-1], wrapped.index(0) + 1, 8 - wrapped[-1], min(7, count), count.bit_length()]

    words = ["110", "010", "000", "101"]

    def odd_one(word, i):
        return all(word[i] != word[j] for j in range(3) if i != j)

    yield (
        359,
        [
            sum(len(set(w)) > 1 for w in words),
            sum(odd_one(w, 1) for w in words),
            sum(w.count("1") >= 2 for w in words),
            sum(len(set(w)) == 1 for w in words),
            sum(odd_one(w, 0) for w in words),
        ],
    )

    def signature(bits):
        a, b, c = bits
        return "".join(str(int(x != y)) for x, y in ((a, b), (b, c), (c, a)))

    signatures = [signature(bits) for bits in itertools.product([0, 1], repeat=3)]
    yield (
        360,
        [
            signature([1, 1, 0]),
            len(set(signatures)),
            signatures.count("000"),
            next(sig[2] for sig in signatures if sig.startswith("10")),
            signature([0, 0, 1]),
        ],
    )


def memory_and_queue():
    def groups(size, cap):
        return [list(range(i, min(size, i + cap))) for i in range(0, size, cap)]

    rows = groups(64, 7)
    yield (
        361,
        [
            len(rows),
            sum(map(len, rows[8:])),
            len(rows[-1]),
            len(groups(64, 4)),
            next(cap for cap in range(1, 65) if len(groups(64, cap)) <= 8),
        ],
    )
    rows = groups(8, 2)
    tests_at = [{int(i in row) for row in rows} for i in range(8)]
    yield (
        362,
        [len(rows), sum(0 not in row for row in rows), sum(map(len, tests_at)), sum(1 for _ in range(8)), 0],
    )

    writes = [(1, 0, 9), (1, 1, 4), (0, 0, 8), (1, 0, 6)]
    queue = [d for wr, full, d in writes if wr and not full]
    rejected = [d for wr, full, d in writes if wr and full]
    yield 363, [len(queue), queue[-1], rejected[0], sum(wr for wr, _, _ in writes) - len(queue), queue[0]]

    expected, reads, cleared, depths = [], [], [], []
    for event in [4, 7, "read", "reset", 2, 8, "read"]:
        if event == "read":
            reads.append(expected.pop(0))
        elif event == "reset":
            cleared.extend(expected)
            expected.clear()
        else:
            expected.append(event)
        depths.append(len(expected))
    yield 364, [reads[1], cleared[0], depths[3], expected[0], max(depths)]


def control_and_delay():
    temperatures = [72, 80, 77, 65, 70]

    def fan(initial):
        states = [initial]
        for temp in temperatures:
            states.append(1 if temp >= 80 else 0 if temp <= 65 else states[-1])
        return states[1:]

    history = fan(0)
    yield (
        365,
        [
            sum(history),
            80 - 65,
            history.index(0, history.index(1)) + 1,
            sum(a != b for a, b in zip([0] + history, history, strict=False)),
            sum(fan(1)),
        ],
    )

    def control(priority):
        previous = 0
        states = []
        for event in ["H", "", "HL", "", "H"]:
            if event:
                previous = int((priority if event == "HL" else event) == "H")
            states.append(previous)
        return states

    low, high = control("L"), control("H")
    yield (
        366,
        [
            sum(low),
            low[2],
            sum(a < b for a, b in zip([0] + low, low, strict=False)),
            sum(high),
            sum(a != b for a, b in zip(low, high, strict=True)),
        ],
    )
    delays = {s: 2 * s + 18 / s + 4 for s in [1, 2, 3, 6]}
    yield (
        367,
        [
            min(delays, key=delays.get),
            delays[2],
            delays[1] - delays[3],
            next(s for s in delays if 2 * s == 18 / s),
            delays[6] - delays[3],
        ],
    )
    table = {load: (18 * (8 - load) + 42 * (load - 2)) / 6 for load in range(2, 9)}
    yield (
        368,
        [
            table[5],
            table[3] - table[2],
            next(k for k, v in table.items() if v == 34),
            table[7] - table[4],
            max(k for k, v in table.items() if v <= 26),
        ],
    )

    old, new = [20, -5, 8], [11, 3, -2]
    differences = [b - a for a, b in zip(old, new, strict=True)]
    yield (
        369,
        [
            differences[1],
            min(new),
            sum(a >= 0 > b for a, b in zip(old, new, strict=True)),
            -min(differences),
            min(new) - min(old),
        ],
    )
    old, new = dict(zip("ABCD", [1, 4, 7, 9], strict=True)), dict(zip("ABCD", [1, 6, 3, 9], strict=True))
    old_order, new_order = sorted(old, key=old.get), sorted(new, key=new.get)
    (missing,) = set(old_order[:2]) - set(new_order[:2])
    rank = new_order.index("B") + 1
    yield (
        370,
        [
            rank,
            len(set(old_order[:2]) & set(new_order[:2])),
            rank,
            new[new_order[1]],
            new[missing] - old[missing],
        ],
    )


def parking_shift_and_encoders():
    occupancy = 49
    levels, rejected, both = [], 0, 0
    for arrive, depart in [(1, 0), (1, 0), (1, 1), (0, 1), (0, 1)]:
        leaving = int(bool(depart and occupancy))
        entering = int(bool(arrive and occupancy - leaving < 50))
        occupancy += entering - leaving
        both += entering * leaving
        rejected += arrive - entering
        levels.append(occupancy)
    yield 371, [levels[-1], rejected, both, levels.count(50), 50 - levels[-1]]

    def shifts(count):
        word = 180
        values = []
        for enabled in [1, 0, 1, 1, 1]:
            if count and enabled:
                count -= 1
                word //= 2
            values.append((word, count))
        return values

    trace = shifts(3)
    complete = next(i for i, (_, count) in enumerate(trace, 1) if count == 0)
    yield 372, [trace[-1][0], trace[1][1], complete, trace[complete - 2][0], shifts(4)[-1][0]]
    active = [2, 6, 9, 11]
    g, local = divmod(max(active), 4)
    yield 373, [local, g, max(set(active) - {11}), len({i // 4 for i in active}), 4 * 3 + 1]
    words = [0] * 4 + [1] * 5 + [2] * 7
    replaced = [min(word, 1) for word in words]
    yield (
        374,
        [
            f"{max(words):02b}",
            words.count(2),
            int(max(words) < 3),
            f"{(0 | 1 | 2):02b}",
            replaced.count(max(replaced)),
        ],
    )

    def cycle(bits):
        states = []
        while bits not in states:
            states.append(bits)
            a, b, c = bits
            bits = str(int(b != c)) + a + b
        return states

    states = cycle("001")
    yield 375, [states[2], len(states), len(cycle("000")), sum(s[2] == "1" for s in states), states[-1]]


def sequential_and_arithmetic():
    def counter(end):
        state, states = 1, []
        for _ in range(12):
            state = 1 if state == end else state + 1
            states.append(state)
        return states

    values = counter(5)
    yield (
        376,
        [values[7], values.index(5) + 1, values.count(1), 8 - len(set(values)), counter(6).index(1) + 1],
    )
    seen = set()
    first_repeat = None
    for step, letter in enumerate("BDBA", 1):
        if letter in seen and first_repeat is None:
            first_repeat = step
        seen.add(letter)
    mask = sum(1 << "ABCD".index(letter) for letter in seen)
    yield 377, [mask, len(seen), first_repeat, 15 ^ mask, len(list(itertools.product([0, 1], repeat=4)))]
    active = [t for t in range(0, 90, 10) if 13 <= t < 46]
    actual = 46 - 13
    yield (
        378,
        [
            len(active),
            actual,
            len(active) * 10 - actual,
            len([t for t in range(0, 90, 10) if 18 <= t < 51]),
            max(active) + 10,
        ],
    )

    pair = [a + b for a, b in itertools.product(range(8), repeat=2)]
    sums = {a + b for a, b in itertools.product(pair, repeat=2)}
    possible = [v * 2 for v in sums]
    constant_zeros = [bit for bit in range(6) if all(((v >> bit) & 1) == 0 for v in possible)]
    yield (
        379,
        [
            max(pair).bit_length(),
            max(sums),
            max(possible).bit_length(),
            constant_zeros[0],
            max(possible) & 31,
        ],
    )
    edges = [2, 3, 6, 7]
    outputs = [edge + 3 for edge in edges]
    yield (
        380,
        [
            outputs[2],
            sum(e <= 8 for e in outputs),
            sum(e <= 7 for e in edges) - sum(e <= 7 for e in outputs),
            len(range(outputs[1] + 1, outputs[2])),
            max(edges) + 4,
        ],
    )
    slots = {width: len(range(0, 8, width)) for width in range(1, 9)}
    yield (
        381,
        [
            min(w for w, count in slots.items() if count <= 5),
            5 - slots[2],
            slots[3] * 3 - 8,
            slots[1],
            min(w for w, count in slots.items() if count <= 3),
        ],
    )
    divs = [divmod(n, 6) for n in range(64)]
    yield (
        382,
        [
            max(q for q, r in divs).bit_length(),
            divs[-1][1],
            next(i for i, (q, _) in enumerate(divs) if q == 8),
            sum(q == 10 for q, r in divs),
            divs.index((5, 4)),
        ],
    )


def sampling_and_analog():
    samples = [1, 1, 0, 1, 0, 0, 1]
    differences = [b - a for a, b in zip([0] + samples, samples, strict=False)]
    yield (
        383,
        [
            differences.count(1),
            differences.count(-1),
            sum(bool(x) for x in differences),
            sum(differences),
            sum(a != b for a, b in zip([1] + samples, samples, strict=False)),
        ],
    )
    steps = [1, 2, 4]
    yield (
        384,
        [
            steps[0] + steps[2],
            (224 >> 1) >> 4,
            len(steps),
            len([v for v in steps if v & 6]),
            8 - max(v >> 7 for v in range(256)).bit_length(),
        ],
    )
    low = list(range(0, 1000, 125))
    recover = [v + 62.5 for v in low]
    yield (
        385,
        [
            low[1] - low[0],
            max(i for i, v in enumerate(low) if v <= 500),
            recover[2],
            max(v - b for v, b in zip(recover, low, strict=True)),
            1000 / 16,
        ],
    )
    low_voltage = 0.0
    for _ in range(100):
        high_voltage = (low_voltage + 3) / 2
        low_voltage = high_voltage / 2
    first_high = 3 / 2
    yield 386, [low_voltage, high_voltage, high_voltage - low_voltage, first_high, first_high / 2]
    period_us = 1 / 2
    frame_us = 5 * period_us
    rate_khz = 1000 / frame_us
    yield 387, [rate_khz, frame_us, 100 * 4 / 5, rate_khz / 2, 1000 / (4 * period_us)]
    power_by_load = {r: (6 / (3 + r)) ** 2 * r for r in range(1, 21)}
    matched = max(power_by_load, key=power_by_load.get)
    current = 6 / (3 + matched)
    yield (
        388,
        [matched, current * matched, current, power_by_load[matched], 100 * current**2 * 3 / (6 * current)],
    )
    capture, arrival = 15 + 5, 3 + 12
    latest = capture - 2
    yield (
        389,
        [
            latest - arrival,
            arrival,
            latest,
            min(t for t in range(30) if t + 5 - 2 >= arrival),
            15 - 2 - arrival,
        ],
    )
    positions = [(row, col) for row in range(3) for col in range(64)]
    first_valid = next(i for i, (row, col) in enumerate(positions, 1) if row >= 2 and col >= 2)
    yield (
        390,
        [
            len(positions) - 64,
            2 * 64 * 2,
            positions[first_valid - 1][0],
            sum(r == 2 and c >= 2 for r, c in positions),
            first_valid,
        ],
    )


def gates_registers_and_thresholds():
    def node(a, b, pull="Z"):
        if a == b:
            return "0" if a else "1"
        return pull

    patterns = list(itertools.product([0, 1], repeat=2))
    yield (
        391,
        [
            node(0, 1),
            sum(node(*p) != "Z" for p in patterns),
            node(1, 1, "1"),
            sum(node(bit, bit) == "Z" for bit in range(2)),
            sum(node(*p, "0") == "1" for p in patterns),
        ],
    )
    s, d = 0, 1
    states = [(s, d)]
    for _ in range(10):
        s, d = s + d, d + 2
        states.append((s, d))
    squares = [s for s, _ in states]
    yield (
        392,
        [
            states[4][1],
            states[5][0],
            states[squares.index(36)][1],
            squares.index(49) - squares.index(9),
            states[5][0] - states[3][0],
        ],
    )
    integer_squares = [k * k for k in range(16)]
    sums = {a + b for a, b in itertools.product(integer_squares, repeat=2)}
    yield (
        393,
        [
            max(sums),
            max(sums).bit_length(),
            max(integer_squares).bit_length(),
            max(sums) & 255,
            integer_squares.index(integer_squares[9] + integer_squares[12]),
        ],
    )
    voltage, trace = 0, []
    for _ in range(5):
        voltage += (900 - voltage) / 2
        trace.append(voltage)
    threshold = 900 * 2 / 3
    yield (
        394,
        [
            next(i for i, v in enumerate(trace, 1) if v >= threshold),
            threshold,
            trace[1],
            900 - trace[2],
            next(i for i, v in enumerate(trace, 1) if v >= 800),
        ],
    )
    floors = set()
    for f in [2, 0, 2]:
        floors.add(f)
    requested = len(floors)
    before = sum(2**f for f in floors)
    floors.remove(0)
    after = sum(2**f for f in floors)
    yield 395, [after, requested, before ^ after, after | 2, len(set(itertools.product([0, 1], repeat=3)))]
    voltages = list(range(800, 1001, 25))
    passed = [v for v in voltages if v < 910]
    fine = list(range(800, 1001, 10))
    yield (
        396,
        [
            voltages[len(passed)],
            max(passed),
            len(passed) + 1,
            len(voltages),
            next(v for v in fine if v >= 910),
        ],
    )

    def fib(enables):
        x, y = 0, 1
        states = [(x, y)]
        for en in enables:
            if en:
                x, y = y, x + y
            states.append((x, y))
        return states

    trace = fib([1, 1, 0, 1, 1])
    yield (
        397,
        [
            sum(trace[-1]),
            trace[3][0],
            sum(trace[0]),
            sum(fib([1] * 5)[-1]),
            sum(sum(a) != sum(b) for a, b in zip(trace, trace[1:], strict=False)),
        ],
    )
    rotations = ["10010101"]
    for _ in range(8):
        previous = rotations[-1]
        rotations.append(previous[-1] + previous[:-1])
    yield (
        398,
        [rotations[1], rotations[5].count("1"), (1 - 3) % 8, rotations[3:].index(rotations[0]), rotations[4]],
    )
    a, b, seventh = "111", "110", 1
    carries = [s.count("1") // 2 for s in [a, b]]
    low = [s.count("1") % 2 for s in [a, b]] + [seventh]
    count = sum(low) + 2 * sum(carries)
    yield 399, [sum(carries), sum(low), count & 1, f"{count:03b}", count - seventh]
    slacks = [(18 - delay, -4 + delay) for delay in range(30)]
    yield (
        400,
        [
            next(d for d, (_, hold) in enumerate(slacks) if hold >= 0),
            max(d for d, (setup, _) in enumerate(slacks) if setup >= 0),
            slacks[7][0],
            slacks[7][1],
            next(d for d, (s, h) in enumerate(slacks) if s == h),
        ],
    )


GROUPS = (
    antenna_and_mirror,
    bytes_and_votes,
    memory_and_queue,
    control_and_delay,
    parking_shift_and_encoders,
    sequential_and_arithmetic,
    sampling_and_analog,
    gates_registers_and_thresholds,
)
REFERENCES = {n: values for group in GROUPS for n, values in group()}
assert set(REFERENCES) == set(range(351, 401))


def format_expected(value):
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).replace("-", "−")


@pytest.mark.parametrize("row,evidence", list(zip(QUIZ, CHECKS, strict=True)), ids=[q["key"] for q in QUIZ])
def test_worked_answer_against_reference(row, evidence):
    n, variant = evidence["task"], row["variant"]
    expected = format_expected(REFERENCES[n][variant - 1])
    assert evidence["expected"] == expected
    assert row["choices"][row["correct"]] == {"he": expected, "en": expected}
    assert len({c["en"] for c in row["choices"]}) == len({c["he"] for c in row["choices"]}) == 4
    assert row["source_key"] == f"quick-hw-{n}"
    assert row["key"] == evidence["key"] == f"quick-hw-{n}-v{variant}"


def test_hardware_shards_are_reproducible_and_link_to_real_interviews():
    author_path = ROOT / "backend/scripts/quiz_authoring/hardware_800.py"
    spec = importlib.util.spec_from_file_location("author_hardware_800", author_path)
    author = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(author)
    assert author.build_bundle(author.LESSONS) == (CARDS, QUIZ, CHECKS)
    interviews = json.loads((ROOT / "interview_preparation/questions.json").read_bytes())["questions"]
    valid = {item["id"] for item in interviews}
    assert len(CARDS) == 50 and len(QUIZ) == len(CHECKS) == 250
    for card in CARDS:
        assert card["interviewIds"] and set(card["interviewIds"]) <= valid
    for lang in ["en", "he"]:
        assert len({q["prompt"][lang] for q in QUIZ}) == len(QUIZ)
