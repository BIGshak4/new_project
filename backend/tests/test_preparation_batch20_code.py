"""Independent finite oracles for the actual PREP-097/098/101 implementations."""
from __future__ import annotations

import importlib.util
import itertools
from collections import Counter
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MATRIX = load("prep_097_sorted_matrix_negatives")
MERGE = load("prep_098_merge_two_sorted_arrays")
TRIPLES = load("prep_101_unique_target_triples")


def check_matrix_cases():
    checked = 0
    for rows in range(4):
        for columns in range(4):
            for flat in itertools.product((-1, 0, 1), repeat=rows * columns):
                matrix = [list(flat[row * columns:(row + 1) * columns]) for row in range(rows)]
                if any(matrix[row][column] > matrix[row][column + 1]
                       for row in range(rows) for column in range(columns - 1)):
                    continue
                if any(matrix[row][column] > matrix[row + 1][column]
                       for row in range(rows - 1) for column in range(columns)):
                    continue
                before = [row[:] for row in matrix]
                assert MATRIX.count_negatives(matrix) == sum(value < 0 for value in flat)
                assert matrix == before
                checked += 1
    with pytest.raises(ValueError):
        MATRIX.count_negatives([[1], [1, 2]])
    assert MATRIX.count_negatives([[-10**100, 0, 10**100]]) == 1
    return checked


def check_merge_cases():
    arrays = [values for length in range(6)
              for values in itertools.combinations_with_replacement((-2, 0, 3), length)]
    checked = 0
    for left, right in itertools.product(arrays, repeat=2):
        result = MERGE.merge_sorted(left, right)
        # Independent frequency reconstruction rather than another cursor merge.
        counts = Counter(left) + Counter(right)
        expected = [value for value in (-2, 0, 3) for _ in range(counts[value])]
        assert result == expected
        assert len(result) == len(left) + len(right)
        checked += 1
    left, right = [1, 4, 4], [2, 4, 7]
    assert MERGE.merge_sorted(left, right) == [1, 2, 4, 4, 4, 7]
    assert left == [1, 4, 4] and right == [2, 4, 7]
    assert MERGE.merge_sorted([], []) == []
    huge = 10**100
    assert MERGE.merge_sorted([-huge, 0], [0, huge]) == [-huge, 0, 0, huge]
    return checked


def check_triple_cases():
    checked = 0
    for length in range(8):
        for values in itertools.product((-1, 0, 1), repeat=length):
            original = list(values)
            for target in range(-3, 4):
                expected = sorted({tuple(sorted(triple))
                                   for triple in itertools.combinations(values, 3)
                                   if sum(triple) == target})
                assert TRIPLES.unique_target_triples(original, target) == expected
                assert original == list(values)
                checked += 1
    assert TRIPLES.unique_target_triples([0] * 100, 0) == [(0, 0, 0)]
    assert TRIPLES.unique_target_triples([1, 1], 3) == []
    assert TRIPLES.unique_target_triples([-1, 0, 1, 2, -1, -4], 0) == [(-1, -1, 2), (-1, 0, 1)]
    huge = 10**100
    assert TRIPLES.unique_target_triples([-huge, 0, huge, huge], 0) == [(-huge, 0, huge)]
    assert len(list(itertools.combinations(range(20), 3))) == 1140
    return checked


def test_sorted_matrix_frontier_matches_every_small_monotone_matrix():
    assert check_matrix_cases() > 0


def test_merge_matches_frequency_reconstruction_and_keeps_every_occurrence():
    assert check_merge_cases() == 3136


def test_unique_value_triples_match_distinct_index_enumeration_then_deduplication():
    assert check_triple_cases() == 22960
