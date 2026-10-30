"""All new code snippets and all115 MCQ cases, using independent small oracles.

Exhaustive tests are bounded model evidence, not native C compilation, formal
proof of every input, hardware timing measurement or human review approval.
"""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
import operator
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
SHARDS = ROOT / "backend/seeds/duel_quiz_batches"
CARDS = json.loads((CONTENT / "fundamentals-code-400.json").read_bytes())
BY_NUMBER = {int(card["id"].split("-")[-1]): card for card in CARDS}
CASES = json.loads((SHARDS / "code_400.checks.json").read_bytes())
QUESTIONS = {q["key"]: q for q in json.loads((SHARDS / "code_400.json").read_bytes())}
OLD_FILES = ("fundamentals-hardware.json", "fundamentals-code-logic.json", "fundamentals-hardware-expansion.json",
             "fundamentals-reasoning-expansion.json", "fundamentals-code-expansion.json",
             "fundamentals-hardware-250.json", "fundamentals-reasoning-250.json", "fundamentals-code-250.json")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def snippet(number, function):
    scope = {}
    exec(compile(BY_NUMBER[number]["code"]["text"], f"short-card-{number}", "exec"), scope)
    return scope[function]


def triples(values, target):
    return {tuple(sorted(values[i] for i in indices)) for indices in itertools.combinations(range(len(values)), 3)
            if sum(values[i] for i in indices) == target}


def longest(values):
    return max((j - i for i in range(len(values)) for j in range(i + 1, len(values) + 1)
                if sum(values[i:j]) % 3 == 0), default=0)


def zero_oracle(values):
    out = copy.deepcopy(values)
    for i, row in enumerate(values):
        for j, value in enumerate(row):
            if value == 0:
                for x in range(len(values)):
                    out[x][j] = 0
                for y in range(len(row)):
                    out[i][y] = 0
    return out


def ordered_parentheses(value):
    history = [0]
    for character in value:
        history.append(history[-1] + (1 if character == "(" else -1 if character == ")" else 0))
    return min(history) >= 0, history[-1] == 0


def graph_data(links):
    seen, path, current = {}, [], 0 if links else None
    while current is not None and current not in seen:
        seen[current] = len(path)
        path.append(current)
        current = links[current]
    entry = current
    cycle_length = len(path) - seen[current] if current is not None else 0
    slow = fast = 0 if links else None
    steps = 0
    while fast is not None and links[fast] is not None:
        slow, fast = links[slow], links[links[fast]]
        steps += 1
        if slow == fast:
            return entry, cycle_length, slow, steps
    return entry, cycle_length, None, steps


def pair_scan(values):
    count = 0

    def less(a, b):
        nonlocal count
        count += 1
        return a < b

    if not values:
        raise ValueError("empty input")
    if len(values) % 2:
        lo = hi = values[0]
        start = 1
    else:
        lo, hi = (values[0], values[1]) if less(values[0], values[1]) else (values[1], values[0])
        start = 2
    for i in range(start, len(values), 2):
        small, large = (values[i], values[i + 1]) if less(values[i], values[i + 1]) else (values[i + 1], values[i])
        if less(small, lo):
            lo = small
        if less(hi, large):
            hi = large
    return lo, hi, count


def oracle(task, data):
    a = data.get("a")
    if task == "matrix_count":
        return sum(value < 0 for row in a for value in row)
    if task == "negative_row_certificate":
        assert data["row"] == sorted(data["row"]) and data["row"][data["j"]] < 0
        return sum(value < 0 for value in data["row"][:data["j"] + 1])
    if task == "staircase_visits":
        i, j, visited = 0, len(a[0]) - 1, []
        while i < len(a) and j >= 0:
            visited.append((i, j))
            if a[i][j] < 0:
                i += 1
            else:
                j -= 1
        assert len(visited) == len(set(visited))
        return len(visited)
    if task == "matrix_missing_order":
        assert all(column == tuple(sorted(column)) for column in zip(*a, strict=True))
        assert any(row != sorted(row) for row in a)
        return "rows"
    if task == "merge_last":
        return sorted(a + data["b"])[-1]
    if task == "merge_all":
        return sorted(a + data["b"])
    if task == "merge_b_prefix":
        merged = sorted(a + data["b"])
        assert merged[:len(data["b"])] == data["b"]
        return merged[:len(data["b"])]
    if task == "forward_overwrite":
        original = list(data["b"])
        assert a[0] < original[0]
        return original[0]
    if task == "triple_index_count":
        return sum(sum(a[i] for i in indices) == data["target"] for indices in itertools.combinations(range(len(a)), 3))
    if task == "triple_unique":
        return len(triples(a, data["target"])) - len(triples(sorted(set(a)), data["target"]))
    if task == "next_anchor":
        return next(i for i in range(data["i"] + 1, len(a)) if a[i] != a[data["i"]])
    if task == "triple_value_count":
        return len(triples(a, data["target"]))
    if task == "first_free":
        return next((i for i in range(data["n"]) if (data["used"] // (2**i)) % 2 == 0), None)
    if task == "bounded_complement":
        return sum(2**i for i in range(data["n"]) if data["used"] // (2**i) % 2 == 0)
    if task == "palindrome":
        return "true" if data["s"] == data["s"][::-1] else "false"
    if task == "palindrome_pairs":
        return len(list(zip(range(len(data["s"]) // 2), range(len(data["s"]) - 1, (len(data["s"]) - 1) // 2, -1), strict=True)))
    if task == "palindrome_checks":
        pairs = [(data["s"][i], data["s"][-1-i]) for i in range(len(data["s"]) // 2)]
        return next((i + 1 for i, (left, right) in enumerate(pairs) if left != right), len(pairs))
    if task in {"free_allocate_head", "free_allocate_result", "free_prepend_link", "free_ownership"}:
        chain = data["free"]
        links = {value: (chain[i + 1] if i + 1 < len(chain) else None) for i, value in enumerate(chain)}
        head = chain[0] if chain else None
        if task == "free_allocate_head":
            return links[head]
        if task == "free_allocate_result":
            return head
        if task == "free_prepend_link":
            links[data["slot"]] = head
            return links[data["slot"]]
        assert data["allocated"] not in chain
        links[data["allocated"]] = data["payload"]
        visited = []
        while head is not None:
            visited.append(head)
            head = links[head]
        return visited
    if task == "double_free_link":
        head, links = None, {}
        for _ in range(2):
            links[data["slot"]] = head
            head = data["slot"]
        return links[data["slot"]]
    if task == "postfix":
        stack = []
        for token in data["tokens"]:
            if isinstance(token, int):
                stack.append(Fraction(token))
                continue
            if len(stack) < 2:
                return "underflow"
            right, left = stack.pop(), stack.pop()
            stack.append({"+": operator.add, "-": operator.sub,
                          "*": operator.mul, "/": operator.truediv}[token](left, right))
        if len(stack) != 1:
            return "extra"
        return int(stack[0]) if stack[0].denominator == 1 else float(stack[0])
    if task == "stack_min":
        remaining = data["push"][:len(data["push"]) - data["pops"]]
        return min(remaining) if remaining else None
    if task == "stack_min_after_replace":
        return min([data["next"]])
    if task == "prefix_minima":
        return [min(a[:i + 1]) for i in range(len(a))]
    if task == "filter_below":
        return [value for value in a if value >= data["t"]]
    if task == "naive_forward_delete":
        values, i = list(a), 0
        while i < len(values):
            if values[i] < data["t"]:
                del values[i]
            i += 1
        return values
    if task == "backward_indices":
        return list(reversed(list(range(data["n"]))))
    if task == "delete_shifts":
        return len(list(range(data["n"]))[data["i"] + 1:])
    if task == "first_equal":
        return next((i for i, value in enumerate(a) if value == data["x"]), -1)
    if task == "lower_bound":
        return sum(value < data["x"] for value in a)
    if task in {"binary_capacity", "binary_fits", "fixed_binary_capacity"}:
        if task == "fixed_binary_capacity":
            return len("0" * data["width"] + "\0")
        digits, value = [], data["n"]
        while value:
            digits.append(value % 2)
            value //= 2
        capacity = len(digits or [0]) + 1
        return capacity if task == "binary_capacity" else "no" if capacity > data["capacity"] else "yes"
    if task in {"tagged_read_blocked", "tagged_pending"}:
        # Filter original request records by identity, independently of the
        # map deletion implementation described in the short card.
        assert len({tag for tag, _ in data["writes"]}) == len(data["writes"])
        remaining = [(tag, address) for tag, address in data["writes"] if tag not in set(data["acked"])]
        if task == "tagged_pending":
            return sorted(tag for tag, _ in remaining)
        return "yes" if any(address == data["read"] for _, address in remaining) else "no"
    if task.startswith("floyd_") or task == "cycle_entry":
        links = data["next"]
        entry, cycle_length, meeting, steps = graph_data(links)
        if task == "cycle_entry":
            return entry
        if task == "floyd_reset_next_pair":
            return [links[0], links[meeting]]
        if task == "floyd_reset_both_bug":
            assert entry != 0
            return 0
        if task == "floyd_meeting_phase":
            assert steps % cycle_length == 0
            return steps % cycle_length
        one, other, count = 0, meeting, 0
        while one != other:
            one, other = links[one], links[other]
            count += 1
        assert one == entry
        return count
    if task == "pair_minmax_count":
        return pair_scan(list(range(data["n"])))[2]
    if task == "minmax_savings":
        return 2 * (data["n"] - 1) - pair_scan(list(range(data["n"])))[2]
    if task == "later_pair_comparisons":
        assert data["min"] < min(data["pair"]) < max(data["pair"]) < data["max"]
        return pair_scan([data["min"], data["max"], *data["pair"]])[2] - 1
    if task == "lex_score":
        scores = data["scores"]
        return sorted(scores, key=lambda score: (score[0], score[1]))[-1]
    if task == "assignment_unique":
        return "no" if len(set(data["assigned"])) != len(data["assigned"]) else "yes"
    if task == "safe_score_weight":
        scores = [(served, first) for served in range(data["n"] + 1) for first in range(served + 1)]
        safe = [weight for weight in data["candidates"] if all(
            weight * left[0] + left[1] > weight * right[0] + right[1]
            for left in scores for right in scores if left[0] > right[0])]
        assert len(safe) == 1
        return safe[0]
    if task == "worker_peak":
        endpoints = sorted({value for start, end, _ in data["intervals"] for value in (start, end)})
        points = [Fraction(value) for value in endpoints]
        points += [Fraction(left + right, 2) for left, right in zip(endpoints, endpoints[1:], strict=False)]
        return max((sum(weight for start, end, weight in data["intervals"]
                        if (start <= point <= end if data["closed"] else start <= point < end)) for point in points), default=0)
    if task == "event_delta":
        return sum(data["starts"]) - sum(data["ends"])
    if task == "spurious_peak":
        wrong = data["old"] + data["starts"]
        actual = max(data["old"], data["old"] + data["starts"] - data["ends"])
        return wrong - actual
    if task == "zero_matrix":
        return zero_oracle(a)
    if task == "zero_markers":
        rows = [i for i, row in enumerate(a) if any(value == 0 for value in row)]
        cols = [j for j in range(len(a[0])) if any(row[j] == 0 for row in a)]
        return [rows, cols]
    if task == "lookup_entries":
        return len(list(itertools.product((0, 1), repeat=data["width"])))
    if task == "lookup_bytes":
        return (2 ** data["width"]) * data["bytes_per_entry"]
    if task == "byte_lookups":
        return len(range(0, data["width"], 8))
    if task == "popcount":
        n, count = data["n"], 0
        while n:
            count += n % 2
            n //= 2
        return count
    if task == "sort_transfers":
        # Count actual tagged read/write events under the declared model.
        stages = 1 if data["model"] == "internal" else 2
        return len([(stage, operation, index) for stage in range(stages) for operation in ("read", "write") for index in range(data["n"])])
    if task == "sorter_call_transfers":
        return sum(len(list(range(data["capacity"]))) for _ in range(data["calls"]) for _ in ("read", "write"))
    if task == "transfer_bytes":
        return sum(data["value_bytes"] for _ in range(data["transfers"]))
    if task == "memory_model_unique":
        costs = {oracle("sort_transfers", {**data, "model": model}) for model in ("internal", "roundtrip")}
        return "no" if len(costs) > 1 else "yes"
    if task in {"permutation_count", "permutation_outputs", "distinct_root_branches"}:
        outputs = sorted({"".join(parts) for parts in itertools.permutations(data["s"])})
        if task == "permutation_outputs":
            return outputs
        if task == "distinct_root_branches":
            return len({output[0] for output in outputs if output})
        return len(outputs)
    if task == "restore_count":
        counts = {character: data["s"].count(character) for character in set(data["s"])}
        before = counts.copy()
        counts[data["char"]] -= 1
        counts[data["char"]] += 1
        assert counts == before
        return counts[data["char"]]
    if task == "earliest_distance":
        return max(data["end"] - index for index in data["previous"])
    if task == "longest_mod3":
        return longest(a)
    if task == "overwrite_earliest_loss":
        last, prefix, wrong = {0: -1}, 0, 0
        for i, value in enumerate(a):
            prefix += value
            remainder = prefix % 3
            if remainder in last:
                wrong = max(wrong, i - last[remainder])
            last[remainder] = i
        return longest(a) - wrong
    if task == "recover_moments":
        candidates = [[x, y] for x in range(1, data["s"]) for y in range(x + 1, data["s"])
                      if x + y == data["s"] and x*x + y*y == data["q"]]
        assert len(candidates) == 1
        return candidates[0]
    if task == "moment_discriminant":
        pair = oracle("recover_moments", data)
        return (pair[1] - pair[0]) ** 2
    if task == "moment_square_valid":
        d = 2 * data["q"] - data["s"] ** 2
        return "yes" if any(x*x == d for x in range(max(0, d) + 1)) else "no"
    if task == "moment_collision":
        assert data["a"] != data["b"]
        same = sum(data["a"]) == sum(data["b"]) and sum(x*x for x in data["a"]) == sum(x*x for x in data["b"])
        return "no" if same else "yes"
    if task.startswith("parenthesis_"):
        value = data["after"] if task == "parenthesis_reset" else data["s"]
        ordered, balanced = ordered_parentheses(value)
        if task == "parenthesis_completable":
            return "true" if ordered else "false"
        return "true" if ordered and balanced else "false"
    raise AssertionError(f"No independent oracle for {task}")


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["key"])
def test_every_mcq_case_matches_an_independent_oracle_and_unique_correct_option(case):
    actual = oracle(case["task"], case["inputs"])
    assert actual == case["expected"]
    question = QUESTIONS[case["key"]]
    matches = [i for i, option in enumerate(case["options"]) if json.dumps(option, sort_keys=True) == json.dumps(actual, sort_keys=True)]
    assert matches == [question["correct"]]
    for language in ("he", "en"):
        assert len({choice[language].strip().casefold() for choice in question["choices"]}) == 4
    assert question["status"] == "draft"


def test_new_card_schema_word_limits_interview_links_and_no_exact_old_duplicates():
    old = [card for name in OLD_FILES for card in json.loads((CONTENT / name).read_bytes())]
    interview_ids = {q["id"] for q in json.loads((ROOT / "interview_preparation/questions.json").read_bytes())["questions"]}
    assert len(old) == 250
    assert len(CARDS) == 23 and set(BY_NUMBER) == set(range(178, 201))
    assert sum(card["topic"] == "python" for card in CARDS) == 7
    for language in ("he", "en"):
        for field in ("title", "prompt"):
            texts = [card[field][language].strip().casefold() for card in old + CARDS]
            assert len(texts) == len(set(texts))
    for card in CARDS:
        assert set(card["interviewIds"]) <= interview_ids
        assert "solution_review" not in card and "company" not in card
        for language in ("he", "en"):
            for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
                assert 0 < len(card[field][language].split()) <= limit
            if language == "en":
                assert not any("\u05d0" <= char <= "\u05ea" for field in ("title", "prompt", "answer", "takeaway") for char in card[field][language])
        if "code" in card:
            assert len(card["code"]["text"].splitlines()) <= 5
    assert "entry" in BY_NUMBER[190]["title"]["en"]
    assert "worst-case" in BY_NUMBER[191]["answer"]["en"]
    assert "visibility" in BY_NUMBER[189]["prompt"]["en"]
    assert "never reused" in BY_NUMBER[189]["prompt"]["en"]


def test_author_rebuild_matches_saved_115_drafts_and_case_specs():
    author = module("code_400_author", ROOT / "backend/scripts/quiz_authoring/code_400.py")
    questions, cases = author.build()
    assert questions == list(QUESTIONS.values()) and cases == CASES
    assert len(questions) == len(cases) == 115
    for card in CARDS:
        variants = [q for q in questions if q["source_key"] == card["id"]]
        assert {q["variant"] for q in variants} == set(range(1, 6))
        for language in ("he", "en"):
            assert len({q["prompt"][language] for q in variants}) == 5
    assembler = module("code_400_text_rules", ROOT / "backend/scripts/quiz_authoring/assemble.py")
    for question in questions:
        for field, pair in [("prompt", question["prompt"]), ("explanation", question["explanation"]),
                            *(("choice", choice) for choice in question["choices"])]:
            for language, text in pair.items():
                assert not assembler.text_issues(text, language, field), (question["key"], field, language)


def test_actual_bitmap_and_palindrome_snippets_exhaustively():
    first_free, palindrome = snippet(181, "first_free"), snippet(182, "palindrome")
    for n in range(9):
        for mask in range(2**n):
            expected = next((i for i in range(n) if mask // 2**i % 2 == 0), None)
            assert first_free(mask, n) == expected
    for n in range(8):
        for chars in itertools.product("AaB", repeat=n):
            value = "".join(chars)
            assert palindrome(value) == (value == value[::-1])


def test_actual_stack_subtraction_and_deletion_snippets():
    subtract, remove = snippet(184, "apply_subtract"), snippet(186, "remove_below")
    for left, right in itertools.product(range(-5, 6), repeat=2):
        stack = [99, left, right]
        subtract(stack)
        assert stack == [99, left - right]
    for length in range(7):
        for values in itertools.product((-1, 0, 2), repeat=length):
            for threshold in (-1, 0, 1, 3):
                a = list(values)
                remove(a, threshold)
                assert a == [value for value in values if value >= threshold]


def test_actual_lower_bound_wrapper_and_binary_capacity_snippets():
    first, capacity = snippet(187, "first_equal"), snippet(188, "binary_capacity")
    for length in range(9):
        for values in itertools.combinations_with_replacement((-2, 0, 2), length):
            for target in range(-3, 4):
                assert first(values, target) == next((i for i, value in enumerate(values) if value == target), -1)
    for n in [*range(65536), 2**64 - 1, 2**80]:
        assert capacity(n) == len(format(n, "b")) + 1


def test_actual_original_zero_and_byte_table_snippets():
    zero, table = snippet(194, "zero_original"), snippet(195, "byte_table")
    for rows in range(4):
        for cols in range(4):
            for cells in itertools.product((0, 1), repeat=rows * cols):
                a = [list(cells[i * cols:(i + 1) * cols]) for i in range(rows)]
                before = copy.deepcopy(a)
                actual = zero(a)
                assert actual == zero_oracle(a) and a == before
                assert all(actual_row is not input_row for actual_row in actual for input_row in a)
    result = table()
    assert isinstance(result, bytes) and len(result) == 256
    for n, value in enumerate(result):
        assert value == sum((n // 2**bit) % 2 for bit in range(8))


def test_actual_exact_moment_and_sticky_stream_snippets():
    recover, feed = snippet(199, "recover_two"), snippet(200, "feed")
    for a, b in itertools.combinations(range(1, 101), 2):
        assert recover(a + b, a*a + b*b) == (a, b)
    huge = 10**30
    assert recover(2 * huge + 3, huge*huge + (huge + 3)**2) == (huge, huge + 3)
    for length in range(9):
        for chars in itertools.product("()x", repeat=length):
            state, prefix = (0, False), ""
            assert state[0] == 0 and not state[1]
            for char in chars:
                state = feed(state, char)
                prefix += char
                ordered, balanced = ordered_parentheses(prefix)
                assert (state[0] == 0 and not state[1]) == (ordered and balanced)
                assert state[0] >= 0


def test_floyd_phase_recovery_and_pairwise_extrema_against_independent_results():
    for tail in range(8):
        for cycle in range(1, 9):
            links = list(range(1, tail + cycle)) + [tail]
            entry, length, meeting, distance = graph_data(links)
            assert entry == tail and length == cycle and distance % cycle == 0
            one, other, moves = 0, meeting, 0
            while one != other:
                one, other = links[one], links[other]
                moves += 1
            assert one == tail and moves == tail
            if tail:
                assert entry != 0, "Resetting both pointers loses the phase relation"
    for length in range(1, 7):
        for values in itertools.permutations(range(length)):
            lo, hi, count = pair_scan(values)
            assert (lo, hi) == (min(values), max(values))
            assert count == (3 * length + 1) // 2 - 2
