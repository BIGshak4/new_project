"""Independent input-derived checks for fifteen cards and all seventy-five cases.

Python snippets are executed. Scope traces specify ordinary C++ lifetime rules;
these are semantic model tests, not native C++ compilation or human attestation.
"""
from __future__ import annotations

import ast
import importlib.util
import itertools
import json
import math
import operator
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
SHARDS = ROOT / "backend/seeds/duel_quiz_batches"
CARDS = json.loads((CONTENT / "fundamentals-code-500.json").read_bytes())
CHECKS = json.loads((SHARDS / "code_500.checks.json").read_bytes())
ROWS = json.loads((SHARDS / "code_500.json").read_bytes())
BY_KEY = {row["key"]: row for row in ROWS}


def snippet(number, name):
    card = next(c for c in CARDS if c["id"] == f"quick-sw-{number}")
    scope = {}
    exec(compile(card["code"]["text"], card["id"], "exec"), scope)
    return scope[name]


def oracle(task, inputs):
    """Read only task inputs; never an authored choice index or expected value."""
    p = inputs
    if task in {"distance2", "closest_distance2", "closest_indices"}:
        if task == "distance2":
            return (p["a"][0] - p["b"][0]) ** 2 + (p["a"][1] - p["b"][1]) ** 2
        candidates = []
        for i, j in itertools.combinations(range(len(p["points"])), 2):
            a, b = p["points"][i], p["points"][j]
            candidates.append(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2, i, j))
        best = min(candidates)
        return best[0] if task == "closest_distance2" else list(best[1:])
    if task == "coordinate":
        y, x = divmod(p["index"], p["width"])
        return [x, y]
    if task == "flatten":
        return p["y"] * p["width"] + p["x"]
    if task == "remaining_pixels":
        return p["width"] * p["height"] - p["used"]
    if task == "next_pixel":
        if p["used"] == len(p["permutation"]):
            return None
        y, x = divmod(p["permutation"][p["used"]], p["width"])
        return [x, y]
    if task == "coordinate_sequence":
        return [[i % p["width"], i // p["width"]] for i in p["indices"]]
    if task == "word_reverse":
        if p["operation"] == "whole":
            return "".join(reversed(p["text"]))
        words = p["text"].split(" ")
        if p["operation"] == "each":
            return " ".join("".join(reversed(w)) for w in words)
        return " ".join(reversed(words))
    if task == "reversal_work":
        # Explicitly sum the sizes rather than copying an algebraic answer.
        return sum(range(p["n"])) if p["kind"] == "concat" else sum(1 for _ in range(p["n"]))
    if task == "list_prepend":
        return [p["value"], *p["list"]] if p["success"] else list(p["list"])
    if task == "new_next":
        return p["old_head"]
    if task == "local_head":
        return p["caller_head"]
    if task == "insertion_link":
        return p["after"]
    if task == "destruction_trace":
        scopes, destroyed = [[]], []
        for operation, value in p["events"]:
            if operation == "construct":
                scopes[-1].append(value)
            elif operation == "enter":
                scopes.append([])
            elif operation == "exit":
                destroyed.extend(reversed(scopes.pop()))
            elif operation in {"throw", "fail_construct"}:
                while scopes:
                    destroyed.extend(reversed(scopes.pop()))
            else:
                raise AssertionError(operation)
        return destroyed
    if task == "delete_trace":
        if p["pointer"] != p["chain"][-1] and not p["virtual"]:
            return "undefined"
        return list(reversed(p["chain"]))
    if task == "tree_stack":
        children = p["children"]

        def height(node):
            return 1 + max((height(child) for child in children[node]), default=0)

        depth = height(0) if children else 0
        return [len(children), depth] if p["kind"] == "work_and_depth" else depth
    if task == "expression":
        tokens = p["tokens"][:-1]
        if p["kind"] == "state":
            cuts = [i for i, token in enumerate(tokens) if token == "+"]
            cut = cuts[-1] if cuts else -1
            previous = expression_value(tokens[:cut]) if cut >= 0 else 0
            return [previous, math.prod(tokens[cut + 1::2])]
        return expression_value(tokens)
    if task == "grammar":
        need_number, finished = True, False
        for token in p["tokens"]:
            if finished:
                return "trailing"
            if need_number:
                if type(token) is not int or token < 0:
                    return "number"
                need_number = False
            elif token == "=":
                finished = True
            elif token in {"+", "*"}:
                need_number = True
            else:
                return "operator"
        return "valid" if finished else "number" if need_number else "terminator"
    if task == "top_two":
        values = p["values"]
        return [[x, values.count(x)] for x in sorted(set(values), reverse=True)[:2]]
    if task == "mode":
        return min(set(p["values"]), key=lambda x: (-p["values"].count(x), x)) if p["values"] else None
    if task == "residual_triple":
        # Reconstruct records, then use actual occurrence counts.
        values = [value for value, count in p["counts"] for _ in range(count)]
        candidates = [value for value in set(values) if values.count(value) % 3 == 1]
        assert len(candidates) == 1
        return candidates[0]
    if task == "draw_line":
        pixels = [int(bool(byte & (1 << bit))) for byte in p["row"] for bit in range(8)]
        pixels[p["x"]:p["x"] + p["length"]] = [1] * p["length"]
        return [sum(pixels[start + bit] * (2 ** bit) for bit in range(8)) for start in range(0, len(pixels), 8)]
    if task == "contains_seven":
        value = p["number"]
        while value:
            value, digit = divmod(value, 10)
            if digit == 7:
                return True
        return False
    if task == "seven_outputs":
        return [value for value in range(p["start"], p["stop"] + 1) if oracle("contains_seven", {"number": value})]
    raise AssertionError(task)


def expression_value(tokens):
    """Independent syntax-tree evaluation; author cases contain only + and *."""
    if not tokens:
        return 0
    tree = ast.parse("".join(map(str, tokens)), mode="eval")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mult)):
            fn = operator.add if isinstance(node.op, ast.Add) else operator.mul
            return fn(visit(node.left), visit(node.right))
        raise AssertionError(ast.dump(node))

    return visit(tree)


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c["key"])
def test_each_mcq_has_one_input_derived_correct_choice(check):
    answer = oracle(check["task"], check["inputs"])
    assert answer == check["expected"]
    assert sum(type(option) is type(answer) and option == answer for option in check["options"]) == 1
    row = BY_KEY[check["key"]]
    assert check["options"][row["correct"]] == answer


def test_short_cards_are_distinct_bilingual_bounded_and_source_linked():
    previous = [card for path in CONTENT.glob("fundamentals-*.json")
                if "500" not in path.name and "revisions" not in path.name
                for card in json.loads(path.read_bytes())]
    assert len(previous) == 400
    assert len(CARDS) == 15 and {c["id"] for c in CARDS} == {f"quick-sw-{n}" for n in range(236, 251)}
    prep_ids = {q["id"] for q in json.loads((ROOT / "interview_preparation/questions.json").read_bytes())["questions"]}
    for card in CARDS:
        assert card["topic"] in {"python", "algorithms"}
        assert card["interviewIds"] and set(card["interviewIds"]) <= prep_ids
        assert "company" not in card and "solution_review" not in card
        for field, cap in [("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)]:
            assert set(card[field]) == {"he", "en"}
            for lang, text in card[field].items():
                assert text == text.strip() and text and len(text.split()) <= cap, (card["id"], field, lang)
                assert "\ufffd" not in text
                if lang == "en":
                    assert not any("\u0590" <= char <= "\u05ff" for char in text)
        if "code" in card:
            assert len(card["code"]["text"].splitlines()) <= 5
    for language, field in itertools.product(("he", "en"), ("title", "prompt")):
        values = [card[field][language].casefold().strip() for card in [*previous, *CARDS]]
        assert len(values) == len(set(values))


def test_five_substantive_drafts_per_card_and_reproducible_artifacts():
    spec = importlib.util.spec_from_file_location("code500", ROOT / "backend/scripts/quiz_authoring/code_500.py")
    author = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(author)
    assert author.build() == (ROWS, CHECKS)
    assert len(ROWS) == len(BY_KEY) == len(CHECKS) == 75
    for card in CARDS:
        group = [row for row in ROWS if row["source_key"] == card["id"]]
        assert sorted(row["variant"] for row in group) == [1, 2, 3, 4, 5]
        for lang in ("he", "en"):
            assert len({row["prompt"][lang] for row in group}) == 5
        assert all(row["status"] == "draft" for row in group)
    for row in ROWS:
        assert row["key"] == f"{row['source_key']}-v{row['variant']}"
        for lang in ("he", "en"):
            assert len({choice[lang] for choice in row["choices"]}) == 4
            for text in [row["prompt"][lang], row["explanation"][lang], *(c[lang] for c in row["choices"])]:
                assert text and text == text.strip() and "\ufffd" not in text
                if lang == "en":
                    assert not any("\u0590" <= char <= "\u05ff" for char in text)
    balance = Counter(row["correct"] for row in ROWS)
    assert max(balance.values()) - min(balance.values()) <= 1


def test_distance_snippet_exhaustive_small_grid_and_duplicate_records():
    function = snippet(236, "distance2")
    points = list(itertools.product(range(-2, 3), repeat=2))
    for a, b in itertools.product(points, repeat=2):
        assert function(a, b) == oracle("distance2", {"a": a, "b": b})
    assert function((10 ** 12, 0), (-10 ** 12, 0)) == 4 * 10 ** 24


def test_coordinate_snippet_preserves_every_small_permutation():
    function = snippet(237, "coordinates")
    for width, height in [(1, 1), (1, 4), (2, 2), (4, 1)]:
        for permutation in itertools.permutations(range(width * height)):
            coordinates = function(permutation, width)
            assert len(set(coordinates)) == width * height
            assert [y * width + x for x, y in coordinates] == list(permutation)
    assert function([], 3) == []


def test_reverse_words_snippet_against_direct_word_order_oracle():
    function = snippet(238, "reverse_words")
    for count in range(5):
        for words in itertools.product(["a", "bc", "D"], repeat=count):
            text = " ".join(words)
            assert function(text) == " ".join(reversed(words))
            assert function(function(text)) == text


def test_mode_snippet_exhaustive_and_order_independent():
    function = snippet(247, "mode_smallest")
    for length in range(6):
        for values in itertools.product([-1, 0, 2], repeat=length):
            assert function(values) == oracle("mode", {"values": values})
            assert function(tuple(reversed(values))) == function(values)


def test_line_snippet_preserves_all_outside_pixels_exhaustively_for_one_byte():
    function = snippet(249, "draw_line")
    for initial in range(256):
        for start in range(9):
            for length in range(9 - start):
                row = [initial]
                out = function(row, start, length)
                assert out is row
                assert out == oracle("draw_line", {"row": [initial], "x": start, "length": length})
    for initial in ([0, 0], [85, 170], [255, 1], [128, 255]):
        for start in range(17):
            for length in range(17 - start):
                assert function(list(initial), start, length) == oracle("draw_line", {"row": initial, "x": start, "length": length})


def test_seven_snippet_matches_arithmetic_digit_scan():
    function = snippet(250, "contains_seven")
    for value in range(10000):
        assert function(value) == oracle("contains_seven", {"number": value})
    assert function(14) is False and function(77) is True and function(0) is False


def test_explicit_boundaries_distinguish_algorithms_and_undefined_behavior():
    assert oracle("reversal_work", {"n": 0, "kind": "concat"}) == 0
    assert oracle("reversal_work", {"n": 5, "kind": "concat"}) == 10
    assert oracle("reversal_work", {"n": 5, "kind": "prepend"}) == 5
    assert oracle("grammar", {"tokens": []}) == "number"
    assert oracle("grammar", {"tokens": [2, "=", "="]}) == "trailing"
    assert oracle("grammar", {"tokens": [2, "*", "+", 3, "="]}) == "number"
    assert oracle("expression", {"tokens": [2, "+", 3, "*", 4, "="], "kind": "value"}) != 20
    assert oracle("delete_trace", {"chain": ["B", "D"], "pointer": "B", "virtual": False}) == "undefined"
    assert oracle("delete_trace", {"chain": ["B", "D"], "pointer": "D", "virtual": False}) == ["D", "B"]
