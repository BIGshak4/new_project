"""Verify the November 14 geometry, reasoning and software reference answers.

Run with a C11 compiler on PATH, or pass e.g. --cc path/to/zig cc.
The checks use only developer-authored local reference implementations.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import runpy
import shutil
import subprocess
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CHECKS = BASE / "checks"
SOLUTIONS = BASE / "solutions"


def test_scoop():
    def segment(a, b):
        return tuple(sorted((a, b)))

    start = {segment((-2, 1), (0, 1)), segment((-2, -1), (0, -1)),
             segment((0, -1), (0, 1)), segment((0, 0), (2, 0))}
    end = {segment((-2, 1), (0, 1)), segment((0, 0), (2, 0)),
           segment((0, 0), (0, 2)), segment((0, 2), (2, 2))}
    ball_x, ball_y = -1, 0
    assert len(start & end) == 2
    assert all(math.dist(a, b) == 2 for a, b in start | end)
    # A half-turn and a vertical translation map the original drawing onto the final one.
    assert {segment((-a[0], 1 - a[1]), (-b[0], 1 - b[1])) for a, b in start} == end
    assert -2 < ball_x < 0 and -1 < ball_y < 1
    assert not (0 < ball_x < 2 and 0 < ball_y < 2)
    return {"checks": ["four segments of equal length", "two stationary sticks",
                       "half-turn congruence", "ball inside only before the moves"]}


def test_vector():
    cases = 0
    for n in range(51):
        a = list(range(n))
        for i in range(n + 1):
            vector = a + [None]
            shifts = 0
            for j in range(n, i, -1):
                vector[j] = vector[j - 1]
                shifts += 1
            vector[i] = -1
            assert vector == a[:i] + [-1] + a[i:] and shifts == n - i
            cases += 1
    capacity = copies = 0
    for n in range(1, 1001):
        if n > capacity:
            copies += n - 1
            capacity = max(1, capacity * 2)
        assert copies < 2 * n
    return {"insertion_indices": cases, "append_prefixes": 1000}


def test_dictionary():
    check = runpy.run_path(str(SOLUTIONS / "prep_314_forbidden_words.py"))["contains_no_forbidden_words"]
    words = ["cat", "Cat", "cat,", "scatter"]
    count = 0
    for size in range(4):
        for tokens in itertools.product(words, repeat=size):
            for mask in range(1 << len(words)):
                dictionary = [w for i, w in enumerate(words) if mask & (1 << i)]
                text = " \t" + "\n \t".join(tokens) + " "
                expected = not any(word == denied for word in tokens for denied in dictionary)
                assert check(text, dictionary) is expected
                count += 1
    return {"string_dictionary_pairs": count}


def test_robots():
    count = 0
    for a, b in itertools.product(range(-4, 5), repeat=2):
        for target in range(-42, 43):
            x = steps = 0
            goal = 1
            d = min(abs(a - target), abs(b - target))
            while a + x != target and b + x != target:
                if x == goal:
                    goal *= -2
                x += 1 if x < goal else -1
                steps += 1
                assert (b + x) - (a + x) == b - a
                assert steps <= 12 * d
            assert steps >= d
            count += 1
    return {"start_and_target_configurations": count, "tested_bound": "d <= moves <= 12*d"}


def test_powers():
    assert 16 ** 18 == 512 ** 8 > 324 ** 8 == 18 ** 16
    assert 8 ** 6 == 512 ** 2 < 1296 ** 2 == 6 ** 8
    return {"exact_integer_comparisons": 2}


def test_tournament():
    for n in range(1, 1025):
        active = n
        games = 0
        while active > 1:
            pairs, bye = divmod(active, 2)
            games += pairs
            active = pairs + bye
        assert games == n - 1
    return {"tournament_sizes": 1024, "matches_for_125": 124}


def test_transpose():
    transpose = runpy.run_path(str(SOLUTIONS / "prep_318_square_transpose.py"))["transpose_in_place"]
    rng = random.Random(318)
    for n in range(18):
        for _ in range(4):
            matrix = [[rng.randrange(-8, 9) for _ in range(n)] for _ in range(n)]
            original = [row[:] for row in matrix]
            ids = list(map(id, matrix))
            assert transpose(matrix) is matrix
            assert list(map(id, matrix)) == ids
            assert matrix == list(map(list, zip(*original)))
            assert transpose(matrix) == original
    return {"square_matrices": 72, "checks": ["independent values", "row and matrix identity", "involution"]}


def test_factorial():
    zeros = runpy.run_path(str(SOLUTIONS / "prep_319_factorial_zeroes.py"))["trailing_zeroes"]
    for n in range(501):
        digits = str(math.factorial(n))
        assert zeros(n) == len(digits) - len(digits.rstrip("0"))
    return {"factorials_checked_directly": 501, "zeros_for_100": zeros(100), "zeros_for_200": zeros(200)}


def test_stack():
    stack = runpy.run_path(str(SOLUTIONS / "prep_131_max_stack.py"))["MaxStack"]
    for bad in [True, None, "3"]:
        try:
            stack().push(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("missing type validation")
    cases = 0
    for length in range(7):
        for ops in itertools.product((None, -1, 0, 1), repeat=length):
            model = []
            s = stack()
            for op in ops:
                if op is None and model:
                    assert s.pop() == model.pop()
                elif op is not None:
                    model.append(op)
                    s.push(op)
                if model:
                    assert s.max() == max(model) and s.top() == model[-1]
                else:
                    for read in (s.max, s.top, s.pop):
                        try:
                            read()
                        except IndexError:
                            pass
                        else:
                            raise AssertionError("missing empty-stack error")
            cases += 1
    return {"operation_sequences": cases, "maximum_sequence_length": 6}


def test_print_binary(cc):
    driver = """#include <limits.h>
#include <stdio.h>
void print_binary(int);
int main(void) {
    int value;
    printf("%d %d\\n", INT_MIN, INT_MAX);
    print_binary(INT_MIN); putchar('\\n');
    print_binary(INT_MAX); putchar('\\n');
    while (scanf("%d", &value) == 1) { print_binary(value); putchar('\\n'); }
    return 0;
}
"""
    values = list(range(-512, 513))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "driver.c").write_text(driver, encoding="ascii")
        binary = root / ("verify.exe" if __import__("os").name == "nt" else "verify")
        subprocess.run([*cc, "-std=c11", "-Wall", "-Wextra", "-Werror", str(SOLUTIONS / "prep_138_print_signed_binary.c"),
                        str(root / "driver.c"), "-o", str(binary)], check=True, cwd=root)
        output = subprocess.run([str(binary)], input="\n".join(map(str, values)) + "\n",
                                text=True, capture_output=True, check=True)
    lines = output.stdout.splitlines()
    lower, upper = map(int, lines[0].split())
    assert lines[1:] == [format(value, "b") for value in (lower, upper, *values)]
    return {"native_c11_inputs": len(values) + 2, "int_limits_checked": [lower, upper]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cc", nargs="+", help="C11 compiler and optional subcommand")
    args = parser.parse_args()
    cc = args.cc or [shutil.which("cc") or shutil.which("clang") or "gcc"]
    for n, check in {312:test_scoop, 313:test_vector, 314:test_dictionary, 315:test_robots,
                     316:test_powers, 317:test_tournament, 318:test_transpose, 319:test_factorial,
                     131:test_stack, 138:lambda: test_print_binary(cc)}.items():
        result = {"question_id": f"PREP-{n:03d}", "passed": True, **check()}
        (CHECKS / f"prep-{n}-1114-verification.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(result)


if __name__ == "__main__":
    main()
