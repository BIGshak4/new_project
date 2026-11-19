"""Independent input-derived checks for 30 cards and every one of 150 cases.

Python snippets execute directly. C/C++ lifetime, ownership and atomic traces
are explicit semantic models, not native compilation or memory-model proofs.
CSV uses Python's independent standard-library parser as the reference.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import io
import itertools
import json
import re
from collections import Counter, deque
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
SHARDS = ROOT / "backend/seeds/duel_quiz_batches"
CARDS = json.loads((CONTENT / "fundamentals-code-700.json").read_bytes())
ROWS = json.loads((SHARDS / "code_700.json").read_bytes())
CHECKS = json.loads((SHARDS / "code_700.checks.json").read_bytes())
BY_KEY = {r["key"]: r for r in ROWS}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def oracle(task, p):
    """Derive results only from independently interpreted inputs."""
    if task == "merge_frontier":
        flattened = sorted(
            (value, row, col) for row, values in enumerate(p["lists"]) for col, value in enumerate(values)
        )
        removed = Counter(row for _, row, _ in flattened[: p["consumed"]])
        return sorted(
            values[removed[row]] for row, values in enumerate(p["lists"]) if removed[row] < len(values)
        )
    if task == "anagram":
        # ASCII-only contract: fold each code point arithmetically.
        return Counter(ord(c) | 32 for c in p["a"]) == Counter(ord(c) | 32 for c in p["b"])
    if task == "anagram_verdict":
        if oracle("anagram", p):
            return "same_counts"
        return "length" if len(p["a"]) != len(p["b"]) else "multiplicity"
    if task == "compact":
        # Stable sort by the Boolean zero class, independently of compaction.
        return sorted(p["values"], key=lambda x: x == 0)
    if task == "reverse_step":
        return [p["current"], p["links"][p["current"]], p["previous"]]
    if task == "csv_record":
        rows = list(csv.reader(io.StringIO(p["record"], newline=""), strict=True))
        assert len(rows) == 1
        return rows[0]
    if task == "key_storage":
        buffer = list(p["original"])
        key = list(buffer) if p["mode"] == "owned" else buffer
        buffer[:] = p["edited"]
        return "".join(key)
    if task == "sudoku_candidates":
        return [
            digit for digit in range(1, 10) if all(digit not in p[region] for region in ("row", "col", "box"))
        ]
    if task == "median_interval":
        # Exhaust every candidate position instead of assuming the median rule.
        positions = p["positions"]
        costs = {x: sum(abs(x - a) for a in positions) for x in range(min(positions), max(positions) + 1)}
        best = [x for x, cost in costs.items() if cost == min(costs.values())]
        return [min(best), max(best)]
    if task == "missing_positive":
        x = 1
        while x in p["values"]:
            x += 1
        return x
    if task == "two_stack_queue":
        queue, results = deque(), []
        for event, value in p["events"]:
            if event == "put":
                queue.append(value)
            else:
                results.append(queue.popleft() if queue else None)
        return results
    if task == "cursor":
        # Interpret as text and a cursor index rather than manipulating stacks.
        text = p["left"] + list(reversed(p["right"]))
        position = len(p["left"])
        if p["operation"] == "right":
            position = min(len(text), position + 1)
        elif p["operation"] == "left":
            position = max(0, position - 1)
        elif p["operation"] == "backspace" and position:
            text.pop(position - 1)
            position -= 1
        elif p["operation"] == "insert":
            text.insert(position, p["value"])
            position += 1
        return [text[:position], list(reversed(text[position:]))]
    if task == "reverse32":
        magnitude, result = abs(p["number"]), 0
        while magnitude:
            magnitude, digit = divmod(magnitude, 10)
            result = 10 * result + digit
        if p["number"] < 0:
            result = -result
        return result if -(2**31) <= result <= 2**31 - 1 else None
    if task == "relative_sort":
        counts = Counter(p["values"])
        result = []
        for value in p["priority"]:
            result.extend([value] * counts.pop(value, 0))
        for value in sorted(counts):
            result.extend([value] * counts[value])
        return result
    if task == "longest_ones":
        # Enumerate all nonempty intervals independently of running counters.
        intervals = [
            (j - i + 1, -i, j)
            for i in range(len(p["bits"]))
            for j in range(i, len(p["bits"]))
            if all(p["bits"][k] == 1 for k in range(i, j + 1))
        ]
        if not intervals:
            return None
        _, negative_start, end = max(intervals)
        return [-negative_start, end]
    if task == "components":
        black = {(row, col) for row, line in enumerate(p["grid"]) for col, pixel in enumerate(line) if pixel}
        count = 0
        while black:
            count += 1
            pending = [black.pop()]
            while pending:
                row, col = pending.pop()
                adjacent = {
                    (r, c)
                    for r, c in black
                    if max(abs(r - row), abs(c - col)) == 1
                    and (p["neighbors"] == 8 or abs(r - row) + abs(c - col) == 1)
                }
                black -= adjacent
                pending.extend(adjacent)
        return count
    if task == "grid_paths":
        # Enumerate direction strings rather than using a DP recurrence.
        h, w = p["height"], p["width"]
        blocked = {tuple(cell) for cell in p["blocked"]}
        total = 0
        for directions in itertools.product("RD", repeat=h + w - 2):
            row = col = 0
            visited = [(row, col)]
            for direction in directions:
                row += direction == "D"
                col += direction == "R"
                visited.append((row, col))
            if (row, col) == (h - 1, w - 1) and not any(cell in blocked for cell in visited):
                total += 1
        return total
    if task == "remove_spaces":
        return p["text"].replace(chr(32), "")
    if task == "atoi_prefix":
        matched = re.match(r" *([+-]?)([0-9]+)", p["text"])
        value = int("".join(matched.groups())) if matched else 0
        return max(-(2**31), min(2**31 - 1, value))
    if task == "circular_move":
        values = p["values"]
        path = [(p["start"] + delta) % len(values) for delta in range(p["steps"] % len(values) + 1)]
        path_values = [values[index] for index in path]
        rotated = path_values[1:] + path_values[:1]
        result = list(values)
        for index, value in zip(path, rotated, strict=True):
            result[index] = value
        return result
    if task == "division":
        return list(divmod(p["dividend"], p["divisor"])) if p["divisor"] > 0 else None
    if task == "copy_mutation":
        a = copy.deepcopy(p["values"])
        b = copy.deepcopy(a) if p["mode"] == "deep" else list(a)
        if p["operation"] == "outer_append":
            b.append(p["value"])
        elif p["operation"] == "outer_replace":
            b[p["index"]] = p["value"]
        elif p["operation"] == "inner_append":
            b[p["index"]].append(p["value"])
        else:
            b[p["index"]][0] = p["value"]
        return [a, b]
    if task == "test_and_set":
        bit, results = p["initial"], []
        for event in p["events"]:
            if event == "tas":
                results.append(bit)
                bit = 1
            else:
                bit = 0
        return [results, bit]
    if task == "local_lifetime":
        if p["mode"] == "automatic":
            return [p["initial"] + delta for delta in p["deltas"]]
        return [p["initial"] + sum(p["deltas"][: index + 1]) for index in range(len(p["deltas"]))]
    if task == "cli_contract":
        if p["status"] != 0:
            return "status"
        return "success" if len(p["stdout"]) > 0 else "output"
    if task == "extract_field":
        data = p["data"]
        if type(data) is not dict or "value" not in data or type(data["value"]) is not str:
            return None
        return data["value"]
    if task == "speed":
        speed = p["initial"]
        for delta in p["actions"]:
            # Independently implement boundary actions, not clamping arithmetic.
            if delta == 1 and speed < 10:
                speed += 1
            elif delta == -1 and speed > 0:
                speed -= 1
        return speed
    if task == "maximum_certainty":
        # An adversarial completion at the upper bound tests the guarantee.
        completed = p["observed"] + [p["upper"]] * p["unknown"]
        if max(completed) != max(p["observed"]):
            return "unknown"
        return "complete" if p["unknown"] == 0 else "upper"
    if task == "undo_branch":
        board = list(p["board"])
        retained = len(p["assignments"]) - p["undo"]
        for index, value in p["assignments"][:retained]:
            assert p["board"][index] == 0
            board[index] = value
        return board
    if task == "merge_pass":
        values, width = p["values"], p["width"]
        for i in range(0, len(values), width):
            assert values[i : i + width] == sorted(values[i : i + width])
        return [
            value for i in range(0, len(values), 2 * width) for value in sorted(values[i : i + 2 * width])
        ]
    if task == "queue_call":
        queue = deque(p["queue"])
        accepted = p["write"] is not None and len(queue) < p["capacity"]
        if accepted:
            queue.append(p["write"])
        read = queue.popleft() if p["read"] and queue else None
        return [accepted, read, list(queue)]
    raise AssertionError(task)


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c["key"])
def test_each_variant_has_exactly_one_independently_derived_answer(check):
    expected = oracle(check["task"], check["inputs"])
    assert canonical(expected) == canonical(check["expected"])
    assert sum(canonical(option) == canonical(expected) for option in check["options"]) == 1
    row = BY_KEY[check["key"]]
    assert canonical(check["options"][row["correct"]]) == canonical(expected)


def test_cards_are_bounded_bilingual_original_and_source_linked():
    assert len(CARDS) == 30
    assert {c["id"] for c in CARDS} == {f"quick-sw-{n}" for n in range(321, 351)}
    prep = {
        q["id"]: q
        for q in json.loads((ROOT / "interview_preparation/questions.json").read_bytes())["questions"]
    }
    editorial = json.loads((ROOT / "backend/seeds/preparation_editorial.json").read_bytes())
    previous = [
        c
        for file in CONTENT.glob("fundamentals-*.json")
        if file.name != "fundamentals-code-700.json" and "revisions" not in file.name
        for c in json.loads(file.read_bytes())
    ]
    for card in CARDS:
        assert card["topic"] in {"python", "algorithms"}
        assert card["interviewIds"] and set(card["interviewIds"]) <= set(prep) & set(editorial)
        assert all(prep[q]["category"] == "software" for q in card["interviewIds"])
        assert not ({"company", "solution_review", "difficulty"} & card.keys())
        for field, cap in [("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)]:
            assert set(card[field]) == {"he", "en"}
            for language, value in card[field].items():
                assert value == value.strip() and 0 < len(value.split()) <= cap, (
                    card["id"],
                    field,
                    language,
                    len(value.split()),
                )
                assert "\ufffd" not in value
                if language == "en":
                    assert not re.search(r"[\u0590-\u05ff]", value)
        if "code" in card:
            assert len(card["code"]["text"].splitlines()) <= 5
            compile(card["code"]["text"], card["id"], "exec")
    for field, language in itertools.product(("title", "prompt"), ("he", "en")):
        prior = {c[field][language].strip().casefold() for c in previous}
        added = [c[field][language].strip().casefold() for c in CARDS]
        assert len(set(added)) == 30
        assert not set(added) & prior


def test_five_substantive_variants_reproducibility_and_internal_evidence():
    spec = importlib.util.spec_from_file_location(
        "code700", ROOT / "backend/scripts/quiz_authoring/code_700.py"
    )
    author = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(author)
    assert author.build_cards() == CARDS
    assert author.build() == (ROWS, CHECKS)
    assert len(ROWS) == len(BY_KEY) == len(CHECKS) == 150
    for card in CARDS:
        rows = [r for r in ROWS if r["source_key"] == card["id"]]
        checks = [c for c in CHECKS if c["key"].startswith(card["id"] + "-v")]
        assert sorted(r["variant"] for r in rows) == [1, 2, 3, 4, 5]
        assert len({canonical(c["inputs"]) for c in checks}) == 5
        assert len({c["source_difficulty"] for c in checks}) == 1
        assert len({c["source_difficulty_rationale"] for c in checks}) == 1
        for check in checks:
            assert type(check["difficulty"]) is int and 1 <= check["difficulty"] <= 10
            assert check["difficulty_rationale"] and check["source_difficulty_rationale"]
            assert 1 <= check["source_difficulty"] <= 10
            assert check["source_content_sha256"] == hashlib.sha256(canonical(card).encode()).hexdigest()
            assert check["provenance"]["interview_ids"] == card["interviewIds"]
            assert check["provenance"]["professional_review"] == "pending"
        for language in ("he", "en"):
            assert len({r["prompt"][language] for r in rows}) == 5
    for row in ROWS:
        assert row["key"] == f"{row['source_key']}-v{row['variant']}"
        assert row["status"] == "draft" and "difficulty" not in row
        for language in ("he", "en"):
            assert len({c[language] for c in row["choices"]}) == 4
            assert len(row["prompt"][language].split()) <= 50
            assert len(row["explanation"][language].split()) <= 65
            for value in [
                row["prompt"][language],
                row["explanation"][language],
                *(c[language] for c in row["choices"]),
            ]:
                assert value and value == value.strip() and "\ufffd" not in value
                if language == "en":
                    assert not re.search(r"[\u0590-\u05ff]", value)
    balance = Counter(r["correct"] for r in ROWS)
    assert max(balance.values()) - min(balance.values()) <= 1


def snippet(number, name):
    card = next(c for c in CARDS if c["id"] == f"quick-sw-{number}")
    scope = {}
    exec(compile(card["code"]["text"], card["id"], "exec"), scope)
    return scope[name]


def test_executed_anagrams_exhaustive_case_mixed_words():
    function = snippet(322, "anagram")
    words = ["".join(chars) for n in range(4) for chars in itertools.product("aAbB", repeat=n)]
    for a, b in itertools.product(words, repeat=2):
        assert function(a, b) == oracle("anagram", dict(a=a, b=b))


def test_executed_compaction_and_missing_positive_exhaustive_small_arrays():
    compact, missing = snippet(323, "compact"), snippet(329, "missing")
    for n in range(6):
        for values in itertools.product((-1, 0, 1, 2), repeat=n):
            assert compact(list(values)) == oracle("compact", dict(values=list(values)))
            assert missing(list(values)) == oracle("missing_positive", dict(values=list(values)))


def test_executed_candidate_sets_all_small_region_combinations():
    function = snippet(327, "candidates")
    subsets = [list(values) for n in range(4) for values in itertools.combinations(range(1, 4), n)]
    for row, col, box in itertools.product(subsets, repeat=3):
        assert function(row, col, box) == oracle("sudoku_candidates", dict(row=row, col=col, box=box))


def test_executed_decimal_reversal_boundaries_and_signed_sample():
    function = snippet(332, "reverse32")
    for number in [*range(-10000, 10001), -(2**31), 2**31 - 1, 1463847412, 1534236469]:
        assert function(number) == oracle("reverse32", dict(number=number))


def test_executed_space_filter_preserves_other_characters_exhaustively():
    function = snippet(337, "remove_spaces")
    for n in range(5):
        for chars in itertools.product(" a\t\n\u00a0", repeat=n):
            value = "".join(chars)
            assert function(value) == oracle("remove_spaces", dict(text=value))


def test_executed_schema_extraction_distinguishes_types():
    function = snippet(345, "extract")
    for data in [
        None,
        [],
        [dict(value="text")],
        {},
        dict(value=None),
        dict(value=2),
        dict(value=False),
        dict(value=""),
        dict(value="text"),
    ]:
        assert function(data) == oracle("extract_field", dict(data=data))


def test_executed_division_exhaustive_small_dividends_and_divisors():
    function = snippet(340, "divide")
    for dividend in range(101):
        for divisor in range(-1, 21):
            assert function(dividend, divisor) == oracle("division", dict(dividend=dividend, divisor=divisor))


def test_executed_saturation_all_short_action_sequences():
    function = snippet(346, "speed")
    for initial in range(11):
        for n in range(8):
            for actions in itertools.product((-1, 1), repeat=n):
                assert function(initial, actions) == oracle("speed", dict(initial=initial, actions=actions))
