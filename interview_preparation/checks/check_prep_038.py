"""Independent brute-force, digit-DP and constructive checks for PREP-038."""
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prep038", ROOT / "solutions/prep_038_adjacent_digits.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def valid(text):
    return all(int(text[i:i + 2]) % 17 == 0 or int(text[i:i + 2]) % 23 == 0
               for i in range(len(text) - 1))


def verify():
    pairs = [17, 23, 34, 46, 51, 68, 69, 85, 92]
    assert list(MODEL.allowed_pairs()) == pairs
    assert not any(pair % 17 == 0 and pair % 23 == 0 for pair in pairs)
    candidates_checked = 0
    for length in range(1, 7):
        brute = set()
        for tail in itertools.product("0123456789", repeat=length - 1):
            text = "3" + "".join(tail)
            candidates_checked += 1
            if valid(text):
                brute.add(text)
        generated = set(MODEL.valid_numbers(length))
        assert generated == brute, length
        assert MODEL.ending_counts(length) == dict(Counter(int(text[-1]) for text in brute)), length

    # Independent DP considers all 100 digit transitions using modular arithmetic,
    # rather than iterating the solver's list of nine positive two-digit numbers.
    # 00 cannot be reached from initial digit 3, so allowing it does not change results.
    counts = [0] * 10
    counts[3] = 1
    target_counts = None
    for length in range(1, 10001):
        expected = {(3, 4, 6, 9, 2)[(length - 1) % 5]: 1}
        tail_length = (length - 3) % 5
        if length >= 4 and tail_length:
            expected[(8, 5, 1, 7)[tail_length - 1]] = 1
        actual = {digit: count for digit, count in enumerate(counts) if count}
        assert actual == expected, (length, actual, expected)
        if length == 2000:
            target_counts = actual
        following = [0] * 10
        for previous in range(10):
            for current in range(10):
                pair = 10 * previous + current
                if pair % 17 == 0 or pair % 23 == 0:
                    following[current] += counts[previous]
        counts = following

    target = MODEL.valid_numbers(2000)
    witnesses = {"34692" * 400, "34692" * 399 + "34685"}
    assert set(target) == witnesses
    assert target_counts == MODEL.ending_counts(2000) == {2: 1, 5: 1}
    assert len(target) == 2
    for text in target:
        assert len(text) == 2000 and text[0] == "3" and valid(text)
    assert {2, 5} == {int(text[-1]) for text in target}

    # Literal all-position-pairs reading already fails for every length-three prefix.
    assert not any(all(int(text[i] + text[j]) in pairs for i in range(3) for j in range(i + 1, 3))
                   for tail in itertools.product("0123456789", repeat=2)
                   for text in ["3" + "".join(tail)])
    # Disjoint blocks would be a different problem: block 34 then arbitrary legal blocks.
    for blocks in (1, 2, 3):
        strings = ["34" + "".join(map(str, rest)) for rest in itertools.product(pairs, repeat=blocks - 1)]
        assert len(strings) == 9 ** (blocks - 1)
        assert {int(s[-1]) for s in strings} == ({4} if blocks == 1 else set(range(1, 10)))
    for length, first in ((0, 3), (-1, 3), (2, 0), (2, 10)):
        try:
            MODEL.ending_counts(length, first)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid parameters accepted")
    report = {
        "question": "PREP-038", "status": "passed",
        "brute_force_candidates_length_1_to_6": candidates_checked,
        "independent_dp_lengths": 10000,
        "target_length": 2000, "target_ending_counts": target_counts,
        "constructive_witnesses_checked": 2,
        "literal_all_pairs_has_solution": False,
        "disjoint_block_interpretation_checked": True,
        "scope": "Exact finite-graph reasoning plus independent models; no human expert review implied."
    }
    return report


if __name__ == "__main__":
    report = verify()
    path = ROOT / "checks/prep-038-verification.json"
    path.write_bytes((json.dumps(report, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8"))
    print(json.dumps(report))
