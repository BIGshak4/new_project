"""Check seven interview-derived short cards and their executable Python helpers."""

from __future__ import annotations

import ast
import itertools
import json
from collections import Counter
from fractions import Fraction
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps" / "web" / "src" / "content"
CARDS = json.loads((CONTENT / "fundamentals-code-250.json").read_text(encoding="utf-8"))
BY_ID = {card["id"]: card for card in CARDS}


def authored_function(number):
    code = BY_ID[f"quick-sw-{number}"]["code"]["text"]
    namespace = {}
    exec(code, namespace)
    functions = [value for key, value in namespace.items() if key != "__builtins__"]
    assert len(functions) == 1 and callable(functions[0])
    return functions[0]


def test_seven_short_bilingual_cards_reference_existing_interview_questions():
    assert len(CARDS) == len(BY_ID) == 7
    assert [card["id"] for card in CARDS] == [f"quick-sw-{number}" for number in range(119, 126)]
    assert Counter(card["topic"] for card in CARDS) == {"algorithms": 6, "python": 1}
    catalog = json.loads((ROOT / "interview_preparation" / "questions.json").read_text(encoding="utf-8"))
    existing_interviews = {question["id"] for question in catalog["questions"]}
    assert [card["interviewIds"] for card in CARDS] == [
        ["PREP-089"], ["PREP-088"], ["PREP-094"], ["PREP-087"],
        ["PREP-080"], ["PREP-037"], ["PREP-026"],
    ]
    previous = []
    for filename in (
        "fundamentals-hardware.json", "fundamentals-code-logic.json",
        "fundamentals-hardware-expansion.json", "fundamentals-code-expansion.json",
        "fundamentals-reasoning-expansion.json",
    ):
        previous.extend(json.loads((CONTENT / filename).read_text(encoding="utf-8")))
    assert len(previous) == 200
    assert not set(BY_ID).intersection(card["id"] for card in previous)
    for card in CARDS:
        assert set(card) <= {"id", "topic", "interviewIds", "title", "prompt", "answer", "takeaway", "code"}
        assert set(card["interviewIds"]) <= existing_interviews
        for field, limit in (("title", 12), ("prompt", 50), ("answer", 65), ("takeaway", 20)):
            assert set(card[field]) == {"he", "en"}
            for language, value in card[field].items():
                assert value.strip() and len(value.split()) <= limit
                assert "\ufffd" not in value
                if language == "he":
                    assert any("\u0590" <= character <= "\u05ff" for character in value)
                if field in {"title", "prompt"}:
                    assert value not in {old[field][language] for old in previous}
        if "code" in card:
            assert card["code"]["language"] == "python"
            code = card["code"]["text"]
            assert 1 <= len(code.splitlines()) <= 5
            assert ";" not in code
            ast.parse(code)


def test_pair_count_multiplicity_matches_index_pair_enumeration():
    assert "four index pairs" in BY_ID["quick-sw-119"]["answer"]["en"]
    assert "one distinct value pair" in BY_ID["quick-sw-119"]["answer"]["en"]
    for length in range(7):
        for values in itertools.product((-1, 0, 1, 2), repeat=length):
            for target in range(-2, 5):
                seen = Counter()
                total = 0
                for value in values:
                    total += seen[target - value]
                    seen[value] += 1
                expected = sum(a + b == target for a, b in itertools.combinations(values, 2))
                assert total == expected
    values = (1, 4, 1, 4)
    matching = [(i, j) for i, j in itertools.combinations(range(4), 2) if values[i] + values[j] == 5]
    assert len(matching) == 4
    assert {tuple(sorted((values[i], values[j]))) for i, j in matching} == {(1, 4)}
    # Inserting before counting would falsely accept this self-pair.
    assert not list(itertools.combinations((2,), 2))


def test_authored_lowest_set_bit_separates_every_small_missing_pair():
    mask_for = authored_function(120)
    for value in range(1, 4096):
        position = 0
        while (value >> position) % 2 == 0:
            position += 1
        assert mask_for(value) == 2 ** position
    for domain_size in range(2, 34):
        for missing in itertools.combinations(range(domain_size), 2):
            present = tuple(value for value in range(domain_size) if value not in missing)
            combined = 0
            for value in itertools.chain(range(domain_size), present):
                combined ^= value
            assert combined != 0
            mask = mask_for(combined)
            assert bool(missing[0] & mask) != bool(missing[1] & mask)
            groups = [0, 0]
            for value in itertools.chain(range(domain_size), present):
                groups[bool(value & mask)] ^= value
            assert set(groups) == set(missing)
    assert mask_for(1 << 1000) == 1 << 1000


def test_authored_byte_reverse_covers_every_input_and_keeps_fixed_width():
    reverse = authored_function(121)
    tree = ast.parse(BY_ID["quick-sw-121"]["code"]["text"])
    assert not any(isinstance(node, (ast.List, ast.Dict, ast.Set, ast.ListComp)) for node in ast.walk(tree))
    for value in range(256):
        expected = int(format(value, "08b")[::-1], 2)
        assert reverse(value) == expected
        assert reverse(reverse(value)) == value
        assert reverse(value).bit_count() == value.bit_count()
    assert reverse(1) == 128 and reverse(0) == 0 and reverse(255) == 255
    assert reverse(0b01101011) == 0b11010110


def test_authored_ray_right_test_matches_exact_fraction_intersection():
    right = authored_function(122)
    tree = ast.parse(BY_ID["quick-sw-122"]["code"]["text"])
    assert not any(isinstance(node, (ast.Div, ast.FloorDiv)) for node in ast.walk(tree))
    checked = 0
    for ax, ay, bx, by, px, py in itertools.product(range(-2, 3), repeat=6):
        if not min(ay, by) < py < max(ay, by):
            continue
        intersection = Fraction(ax) + Fraction((py - ay) * (bx - ax), by - ay)
        if intersection == px:
            continue
        expected = intersection > px
        assert right(ax, ay, bx, by, px, py) is expected
        assert right(bx, by, ax, ay, px, py) is expected
        checked += 1
    assert checked == 2296
    # Large integer translation must not introduce float rounding.
    offset = 10 ** 100
    assert right(offset + 2, offset - 1, offset + 2, offset + 1, offset, offset)
    assert right(offset + 2, offset + 1, offset + 2, offset - 1, offset, offset)
    assert not right(offset - 2, offset - 1, offset - 2, offset + 1, offset, offset)


def trial_prime(value):
    return value >= 2 and all(value % divisor for divisor in range(2, value))


def test_sieve_square_start_preserves_exactly_the_primes():
    for limit in range(501):
        flags = [False, False] + [True] * max(0, limit - 1)
        flags = flags[:limit + 1]
        for prime in range(2, limit + 1):
            if not flags[prime]:
                continue
            for multiple in range(prime * prime, limit + 1, prime):
                flags[multiple] = False
        assert flags == [trial_prime(value) for value in range(limit + 1)]
    for prime in range(2, 101):
        if not trial_prime(prime):
            continue
        smaller_primes = [value for value in range(2, prime) if trial_prime(value)]
        for multiplier in range(2, prime):
            assert any((prime * multiplier) % divisor == 0 for divisor in smaller_primes)
    assert not trial_prime(25) and trial_prime(5)


def stack_valid(text):
    stack = []
    matching = {")": "(", "]": "[", "}": "{"}
    for character in text:
        if character in "([{":
            stack.append(character)
        elif character in matching and (not stack or stack.pop() != matching[character]):
            return False
    return not stack


def deletion_oracle(text):
    text = "".join(character for character in text if character in "()[]{}")
    while True:
        shorter = text.replace("()", "").replace("[]", "").replace("{}", "")
        if shorter == text:
            return not text
        text = shorter


def test_typed_bracket_stack_matches_independent_adjacent_deletion():
    assert not stack_valid("([)]")
    assert all("([)]".count(opener) == "([)]".count(closer) for opener, closer in zip("([{", ")]}", strict=True))
    for length in range(7):
        for characters in itertools.product("()[]{}", repeat=length):
            text = "".join(characters)
            assert stack_valid(text) == deletion_oracle(text)
    for text in ("", "letters", "a{b[c](d)}", "aa)a(a", "a((", "]"):
        assert stack_valid(text) == deletion_oracle(text)


@cache
def shapes(size):
    if not size:
        return (None,)
    return tuple(
        (left, right)
        for left_size in range(size)
        for left in shapes(left_size)
        for right in shapes(size - 1 - left_size)
    )


def label_shape(shape, labels):
    if shape is None:
        return None
    return (next(labels), label_shape(shape[0], labels), label_shape(shape[1], labels))


def tree_values(tree):
    if tree is None:
        return []
    return [tree[0], *tree_values(tree[1]), *tree_values(tree[2])]


def is_bst(tree, lower=None, upper=None):
    if tree is None:
        return True
    value, left, right = tree
    return (
        (lower is None or value > lower)
        and (upper is None or value < upper)
        and is_bst(left, lower, value)
        and is_bst(right, value, upper)
    )


def test_rightmost_maximum_requires_global_search_tree_order():
    counterexamples = 0
    for size in range(1, 6):
        for shape in shapes(size):
            for labels in itertools.product((-1, 0, 1), repeat=size):
                tree = label_shape(shape, iter(labels))
                last = tree
                while last[2] is not None:
                    last = last[2]
                maximum = max(tree_values(tree))
                if is_bst(tree):
                    assert last[0] == maximum
                elif last[0] != maximum:
                    counterexamples += 1
    assert counterexamples > 0
    tree = (3, (99, None, None), (4, None, None))
    assert max(tree_values(tree)) == 99 and tree[2][0] == 4
    assert not is_bst(tree)
