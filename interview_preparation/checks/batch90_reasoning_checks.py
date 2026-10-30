"""Independent finite oracles for six proposed intake explanations.

These are mathematical/software checks, not hardware or live-user tests.
"""

import importlib.util
import itertools
import json
import math
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOLUTIONS = HERE.parent / "solutions"


def load(number, name):
    path = SOLUTIONS / f"prep_{number}_{name}.py"
    spec = importlib.util.spec_from_file_location(f"prep_{number}_checked", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_182():
    model = load(182, "turtle_return")
    words = steps = 0
    for length in range(10):
        for commands in itertools.product("RLM", repeat=length):
            position, direction = 0j, 1 + 0j
            for command in commands:
                if command == "R":
                    direction *= -1j
                elif command == "L":
                    direction *= 1j
                else:
                    position += direction
            x, y, heading = model.turtle_state(commands)
            assert complex(x, y) == position
            assert model.returns_to_start(commands) == (position == 0)
            assert complex(*model.VECTORS[heading]) == direction
            words += 1
            steps += length
    assert model.returns_to_start("MRMRMRM")
    assert model.turtle_state("MRMRMRM")[2] != 0
    for invalid in ("m", "MX", "M R"):
        try:
            model.turtle_state(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid command accepted")
    return {"status": "passed", "words_checked": words, "command_steps": steps,
            "method": "Exhaustive words through length 9 versus independent complex-number rotations; position and orientation compared separately.",
            "edge_cases": ["empty", "turns only", "return with changed heading", "invalid symbols"],
            "limitation": "Finite enumeration supports the stated induction; no physical turtle tested."}


def check_183():
    model = load(183, "cube_surface_path")
    checked = 0
    for side in (0.125, 0.5, 1, 2, 3, 7, 10, 20, 100):
        optimum = model.shortest_surface_length(side)
        assert math.isclose(optimum * optimum, 5 * side * side, rel_tol=1e-12)
        assert math.isclose(model.path_via_shared_edge(side, side / 2), optimum, rel_tol=1e-12)
        for numerator in range(101):
            offset = side * numerator / 100
            # Independent 3D broken-line oracle through P=(side,offset,0).
            first = math.dist((0, 0, 0), (side, offset, 0))
            second = math.dist((side, offset, 0), (side, side, side))
            actual = model.path_via_shared_edge(side, offset)
            assert math.isclose(actual, first + second, rel_tol=1e-12)
            assert actual >= optimum - 1e-10 * max(1, side)
            checked += 1
        assert math.sqrt(3) * side < optimum < (1 + math.sqrt(2)) * side < 3 * side
    rejected = 0
    for side in (0, -1, float("nan"), float("inf")):
        try:
            model.shortest_surface_length(side)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("Invalid side accepted")
    return {"status": "passed", "edge_crossing_samples": checked, "invalid_sides_rejected": rejected,
            "method": "Independent 3D Euclidean segment sums; midpoint construction; analytic lower bound in explanation uses the near/far-face separator and triangle inequality.",
            "minimum_unit_length_squared": 5,
            "limitation": "Samples do not establish continuous minimality; the separate separator proof does."}


def check_184():
    model = load(184, "random5_to_random7")
    accepted = Counter()
    rejected = []
    for first, second in itertools.product(range(5), repeat=2):
        value = 5 * first + second
        if value < 21:
            calls = iter((first, second))
            result = model.random7(calls.__next__)
            assert result == value % 7
            accepted[result] += 1
        else:
            rejected.append((first, second))
    assert accepted == Counter({value: 3 for value in range(7)})
    histories = 0
    for depth in range(1, 5):
        counts = Counter()
        for rejected_prefix in itertools.product(rejected, repeat=depth - 1):
            for accepted_value in range(21):
                draws = [digit for pair in rejected_prefix for digit in pair]
                draws += list(divmod(accepted_value, 5))
                iterator = iter(draws)
                answer = model.random7(iterator.__next__)
                counts[answer] += 1
                histories += 1
                try:
                    next(iterator)
                except StopIteration:
                    pass
                else:
                    raise AssertionError("Returned before consuming scripted accepted attempt")
        assert len(set(counts.values())) == 1 and len(counts) == 7
    expected_calls = Fraction(2, 1) / Fraction(21, 25)
    assert expected_calls == Fraction(50, 21)
    for bound in range(1, 12):
        assert 5**bound % 7 != 0
    return {"status": "passed", "uniform_pair_cases": 25, "accepted_counts": dict(accepted),
            "scripted_first_accept_histories": histories, "expected_random5_calls": "50/21",
            "method": "Exact enumeration of 25 equiprobable pairs and every rejection prefix through 4 attempts; rational expectation and fixed-call divisibility check.",
            "limitation": "Uniformity assumes the supplied random5 draws are independent and uniform. No statistical RNG certification; no finite worst-case termination bound."}


def check_185():
    model = load(185, "digit_seven_boom")
    count = 0
    flags = model.seven_flags(1_000_000)
    for number, actual in flags:
        expected = "7" in str(number)
        assert actual == expected
        assert model.contains_seven(number) == expected
        count += actual
    assert count == 1_000_000 - 9**6 == 468559
    small = list(model.seven_boom(100))
    assert small == ["boom"] * 19
    assert list(model.seven_boom(6)) == []
    assert list(model.seven_boom(7)) == ["boom"]
    assert list(model.seven_boom(14)) == ["boom"]  # 14 itself emits nothing.
    assert len(list(model.seven_boom(77))) - len(list(model.seven_boom(76))) == 1
    assert sum(1 for _ in model.seven_boom(1_000_000)) == count
    assert list(model.seven_boom(0)) == [] and not model.contains_seven(0)
    return {"status": "passed", "integers_checked": 1_000_000, "booms_through100": 19,
            "booms_through1000000": count,
            "method": "Both numerical digit scanning and incremental digit-state outputs versus independent decimal-string membership for every input 1..1000000; combinatorial count 1e6-9^6; actual boom-only generator checked through one million.",
            "limitation": "The rule emits boom once per matching number and nothing for nonmatches; divisibility by 7 is not a source requirement. Printing throughput not benchmarked."}


def check_186():
    model = load(186, "fence_crossing_anchor")
    checked = 0
    for length in range(14):
        for events in itertools.product((False, True), repeat=length):
            for initial in (False, True):
                state = initial
                for event in events:
                    if event:
                        state = not state
                assert model.infer_initial_inside(events, final_inside=state) == initial
                if not state:
                    assert model.from_outside_coast(events) == initial
                checked += 1
    geometric = 0
    # Bounded rectangular island and a wholly internal rectangular closed fence.
    for x in range(-9, 10):
        for y in range(-9, 10):
            if x in (-3, 3) or y in (-2, 2):
                continue
            # Walk east to coastline x=10. Vertical edges are crossed only
            # strictly between their endpoints; start is never on the fence.
            crossing_x = [edge for edge in (-3, 3) if x < edge and -2 < y < 2]
            inferred = model.from_outside_coast([True] * len(crossing_x))
            assert inferred == (-3 < x < 3 and -2 < y < 2)
            geometric += 1
    try:
        model.infer_initial_inside((True, False))
    except ValueError:
        pass
    else:
        raise AssertionError("Unanchored answer fabricated")
    return {"status": "passed", "anchored_histories_checked": checked,
            "rectangular_geometric_rays": geometric,
            "method": "All binary crossing histories through length 13 for both initial states versus direct toggling; synthetic finite-island geometry and unknown-anchor rejection.",
            "limitation": "The coastal anchor requires the explicit fence/topology/motion promises in the explanation. Bare crossing and sea sensors alone do not establish them."}


def check_187():
    model = load(187, "reverse_words_reuse")
    words = intervals = 0
    for length in range(9):
        for letters in itertools.product("ab ", repeat=length):
            original = "".join(letters)
            expected = "".join(reversed(re.findall(r" +|[^ ]+", original)))
            result = model.reverse_words(original)
            assert result == expected
            assert model.reverse_words(result) == original
            assert Counter(result) == Counter(original)
            words += 1
            if length <= 4:
                for left in range(length + 1):
                    for right in range(left - 1, length):
                        chars = list(original)
                        model.reverse_range(chars, left, right)
                        target = original[:left] + original[left:right + 1][::-1] + original[right + 1:]
                        assert "".join(chars) == target
                        intervals += 1
    assert model.reverse_words("I am an engineer") == "engineer an am I"
    assert model.reverse_words("  ab c ") == " c ab  "
    assert model.reverse_words("אב ג") == "ג אב"
    assert model.reverse_words("a\tb c") == "c a\tb"
    return {"status": "passed", "strings_checked": words, "range_reversals_checked": intervals,
            "method": "All strings over a,b,space through length 8 versus independent reversed-token oracle; involution and character multiplicity; every inclusive/empty range through length 4.",
            "limitation": "Words use ASCII space as delimiter; tabs/punctuation are word content. Python strings are copied by the wrapper; in-place mutable-buffer operation uses constant extra words."}


def run(number):
    result = globals()[f"check_{number}"]()
    result["question_id"] = f"PREP-{number}"
    result["ai_assisted"] = True
    result["professional_review"] = "pending"
    (HERE / f"prep-{number}-verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    for question_number in (182, 183, 184, 185, 186, 187):
        run(question_number)
