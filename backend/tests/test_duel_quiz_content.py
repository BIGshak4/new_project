"""Check the authored quiz batch against its real short sources and independent oracles.

These tests do not grant human editorial approval. Production still requires approved status.
"""

import itertools
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = json.loads((ROOT / "backend/seeds/duel_quiz.json").read_text(encoding="utf-8"))
LINKED = {q["key"]: q for q in SEED["questions"] if q.get("source_key")}


def answer(key, language="en"):
    q = LINKED[key]
    return q["choices"][q["correct"]][language]


def test_linked_batch_has_ten_real_sources_and_five_bilingual_variants_each():
    source_cards = {}
    for path in (ROOT / "apps/web/src/content").glob("fundamentals-*.json"):
        content = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(content, list):
            source_cards.update({c["id"]: c for c in content})
    groups = defaultdict(list)
    assert len(LINKED) == 50
    assert len({q["key"] for q in SEED["questions"]}) == len(SEED["questions"])
    for q in LINKED.values():
        assert q["source_key"] in source_cards
        assert q["key"] == f"{q['source_key']}-v{q['variant']}"
        assert q["status"] in {"draft", "approved"}
        assert type(q["correct"]) is int and 0 <= q["correct"] < 4
        assert len(q["choices"]) == 4
        for lang in ("he", "en"):
            assert q["prompt"][lang].strip()
            assert q["explanation"][lang].strip()
            choices = [c[lang].strip() for c in q["choices"]]
            assert all(choices)
            assert len(set(choices)) == 4, q["key"]
        groups[q["source_key"]].append(q)
    assert len(groups) == 10
    for variants in groups.values():
        assert sorted(q["variant"] for q in variants) == [1, 2, 3, 4, 5]
        for lang in ("he", "en"):
            assert len({q["prompt"][lang] for q in variants}) == 5


def test_xor_variants_against_truth_table():
    assert answer("quick-hw-03-v1") == "XOR"
    assert answer("quick-hw-03-v2") == ", ".join(str(a ^ b) for a, b in [(0, 0), (0, 1), (1, 1)])
    differences = [(a, b) for a, b in itertools.product((0, 1), repeat=2) if (a | b) != (a ^ b)]
    assert differences == [(1, 1)]
    assert answer("quick-hw-03-v3") == "A=1, B=1"
    candidates = [b for b in (0, 1) if 1 ^ b == 1]
    assert candidates == [int(answer("quick-hw-03-v4"))]
    assert answer("quick-hw-03-v5") == "(A AND NOT B) OR (NOT A AND B)"
    for a, b in itertools.product((0, 1), repeat=2):
        assert (a ^ b) == ((a and not b) or (not a and b))


def test_mux_variants_against_selector():
    def mux(d0, d1, s):
        return (d0, d1)[s]

    assert answer("quick-hw-05-v1") == str(mux(0, 1, 0))
    assert answer("quick-hw-05-v2") == ", ".join(str(mux(1, 0, s)) for s in (0, 1))
    assert all(mux(1, 1, s) == 1 for s in (0, 1))
    assert answer("quick-hw-05-v3") == "Always 1"
    assert answer("quick-hw-05-v4") == "D1"
    assert all(mux(0, 1, s) == s for s in (0, 1))
    assert answer("quick-hw-05-v5") == "D0=0, D1=1"


def test_unsigned_width_variants():
    assert int(answer("quick-hw-09-v1")) == 2**5 - 1
    assert int(answer("quick-hw-09-v2")) == len(list(itertools.product((0, 1), repeat=3)))
    assert int(answer("quick-hw-09-v3")) == next(n for n in range(1, 10) if 2**n > 20)
    assert answer("quick-hw-09-v4") == f"0..{2**6 - 1}"
    assert int(answer("quick-hw-09-v5")) == 2**5 // 2**4


def test_authored_truncated_sums_from_actual_prompt_numbers():
    for n in range(1, 6):
        key = f"quick-hw-10-v{n}"
        prompt = LINKED[key]["prompt"]["en"]
        a, b, width = map(int, re.findall(r"\d+", prompt))
        expected = (a + b) & ((1 << width) - 1)
        assert answer(key) == str(expected)
        assert answer(key, "he") == str(expected)


def test_flip_flop_variants_with_valid_sampling_edges():
    assert answer("quick-hw-15-v1") == "1"  # No rising edge: previous Q retained.
    assert answer("quick-hw-15-v2") == "0, 1"  # D sampled at successive valid edges.
    assert answer("quick-hw-15-v3") == "0"  # Falling edge is not active.
    assert answer("quick-hw-15-v4") == "0"  # Pulse ended before valid sampling edge.
    assert answer("quick-hw-15-v5") == "1, 0, 1"
    for n in range(1, 6):
        assert "no reset" in LINKED[f"quick-hw-15-v{n}"]["prompt"]["en"]


def test_authored_counter_variants_from_actual_prompt_numbers():
    for n in range(1, 6):
        key = f"quick-hw-21-v{n}"
        width, start, edges, stated_width = map(int, re.findall(r"\d+", LINKED[key]["prompt"]["en"]))
        assert width == stated_width
        value = start
        for _ in range(edges):
            value = (value + 1) & ((1 << width) - 1)
        assert answer(key) == str(value)


def test_authored_binary_variants_from_actual_words():
    for n in range(1, 6):
        key = f"quick-hw-40-v{n}"
        word = re.search(r"number ([01]+)\?", LINKED[key]["prompt"]["en"]).group(1)
        value = sum(int(bit) * 2**i for i, bit in enumerate(reversed(word)))
        assert answer(key) == str(value)


def test_authored_parallel_machine_variants_by_capacity_lower_bound():
    for n in range(1, 6):
        key = f"quick-sw-02-v{n}"
        machines, duration, jobs = map(int, re.findall(r"\d+", LINKED[key]["prompt"]["en"]))
        result = int(answer(key))
        assert machines * (result // duration) >= jobs
        assert machines * ((result - 1) // duration) < jobs
        assert result == math.ceil(jobs / machines) * duration


def test_authored_first_even_variants_execute_original_source_function():
    source = json.loads((ROOT / "apps/web/src/content/fundamentals-code-logic.json").read_text(encoding="utf-8"))
    code = next(c for c in source if c["id"] == "quick-sw-03")["code"]["text"]
    scope = {}
    exec(code, scope)  # Trusted, committed source function; not arbitrary user content.
    for n in range(1, 6):
        key = f"quick-sw-03-v{n}"
        values = json.loads(re.search(r"(\[[^\]]*\])", LINKED[key]["prompt"]["en"]).group(1))
        assert answer(key) == str(scope["first_even"](values))


def test_midpoint_examples_and_necessary_sufficient_condition():
    def midpoint(a, b):
        return tuple((x + y) / 2 for x, y in zip(a, b, strict=True))

    assert midpoint((2, 5), (8, 1)) == (5, 3)
    assert answer("quick-sw-61-v1") == "(5,3)"
    assert answer("quick-sw-61-v2") == "(1,2), (5,8)"
    pair_choices = [((1, 2), (5, 8)), ((1, 2), (4, 8)), ((2, 1), (4, 6)), ((0, 0), (1, 1))]
    assert [all(v.is_integer() for v in midpoint(a, b)) for a, b in pair_choices] == [True, False, False, False]
    assert midpoint((1, 2), (2, 1)) == (1.5, 1.5)
    assert answer("quick-sw-61-v3") == "(1.5,1.5)"
    assert "necessary and sufficient" in LINKED["quick-sw-61-v4"]["prompt"]["en"]
    assert answer("quick-sw-61-v4") == "The x values have the same parity, and so do the y values"
    for ax, ay, bx, by in itertools.product(range(-3, 4), repeat=4):
        exact = all(v.is_integer() for v in midpoint((ax, ay), (bx, by)))
        assert exact == (ax % 2 == bx % 2 and ay % 2 == by % 2)
    assert midpoint((-3, 4), (5, -2)) == (1, 1)
    assert answer("quick-sw-61-v5") == "(1,1)"
