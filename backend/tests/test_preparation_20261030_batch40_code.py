"""Independent finite oracles for four new software questions and width reversal."""
from __future__ import annotations

import importlib.util
import itertools
import random
from fractions import Fraction
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COSTUMES = load("prep_148_costume_preferences")
WORKERS = load("prep_149_worker_interval_peak")
MATRIX = load("prep_150_zero_matrix_original")
COUNT = load("prep_151_byte_popcount")
REVERSE = load("prep_094_given_width_reversal")


def assignment_oracle(costumes, preferences):
    """Enumerate all named costumes, including unacceptable ones, then filter."""
    best = (0, 0)
    for assignment in itertools.product((*costumes, None), repeat=len(preferences)):
        used = [item for item in assignment if item is not None]
        if len(set(used)) != len(used):
            continue
        if any(item is not None and item not in choices
               for item, choices in zip(assignment, preferences, strict=True)):
            continue
        served = len(used)
        first = sum(bool(choices) and item == choices[0]
                    for item, choices in zip(assignment, preferences, strict=True))
        best = max(best, (served, first))
    return best


def assignment_case(costumes, preferences):
    original = tuple(tuple(person) for person in preferences)
    result = COSTUMES.best_costume_assignment(costumes, preferences)
    assert result["score"] == assignment_oracle(costumes, preferences)
    assignment = result["assignment"]
    assert len(assignment) == len(preferences)
    used = [item for item in assignment if item is not None]
    assert len(set(used)) == len(used)
    assert all(item is None or item in choices
               for item, choices in zip(assignment, preferences, strict=True))
    assert result["score"] == (len(used), sum(bool(choices) and item == choices[0]
                                            for item, choices in zip(assignment, preferences, strict=True)))
    assert tuple(tuple(person) for person in preferences) == original


def check_costume_cases():
    cases = 0
    for m in range(5):
        costumes = tuple("abcde"[:m])
        options = [()]
        options.extend((item,) for item in costumes)
        options.extend(itertools.permutations(costumes, 2))
        for n in range(4):
            for preferences in itertools.product(options, repeat=n):
                assignment_case(costumes, preferences)
                cases += 1
    rng = random.Random(148)
    costumes = tuple("abcde")
    for _ in range(60):
        preferences = [tuple(rng.sample(costumes, rng.randrange(3))) for _ in range(rng.randrange(7))]
        assignment_case(costumes, preferences)
    source_preferences = [("a", "b"), ("c", "a"), ("d", "e"), ("d", "b")]
    source = COSTUMES.best_costume_assignment(costumes, source_preferences)
    assert source["score"] == (4, 3)
    # Maximizing first choices alone can sacrifice accepted allocations.
    witness = COSTUMES.best_costume_assignment(("a", "b"), [("a", "b"), ("a",)])
    assert witness == {"assignment": ("b", "a"), "score": (2, 1)}
    for inventory, preferences in [(["a", "a"], []), (["a"], [("x",)]), (["a"], [("a", "a")])]:
        with pytest.raises(ValueError):
            COSTUMES.best_costume_assignment(inventory, preferences)
    return {"exhaustive_inventory_preference_cases": cases, "seeded_cases": 60,
            "four_person_source_score": [4, 3], "fifth_person_invented": False,
            "lexicographic_priority_witness_checked": True}


def integer_worker_oracle(intervals):
    if not intervals:
        return 0
    return max(sum(demand for start, end, demand in intervals if start <= day <= end)
               for day in range(min(start for start, _, _ in intervals),
                                max(end for _, end, _ in intervals) + 1))


def continuous_worker_oracle(intervals):
    if not intervals:
        return 0
    points = sorted({x for start, end, _ in intervals for x in (start, end)})
    probes = points + [(left + right) / 2 for left, right in itertools.pairwise(points)]
    return max(sum(demand for start, end, demand in intervals if start <= point < end)
               for point in probes)


def check_worker_cases():
    counts = {}
    for mode, endpoints, oracle in [
        ("integer_inclusive", tuple(range(4)), integer_worker_oracle),
        ("continuous_half_open", tuple(Fraction(i, 2) for i in range(4)), continuous_worker_oracle),
    ]:
        options = [(start, end, demand) for start in endpoints for end in endpoints
                   if start <= end for demand in range(3)]
        cases = 0
        for length in range(4):
            for source in itertools.product(options, repeat=length):
                assert WORKERS.minimum_workers(source, mode=mode) == oracle(source)
                cases += 1
        rng = random.Random(149)
        for _ in range(150):
            intervals = []
            for _ in range(rng.randrange(20)):
                left, right = sorted((rng.randrange(-20, 21), rng.randrange(-20, 21)))
                if mode == "continuous_half_open":
                    left, right = Fraction(left, 3), Fraction(right, 3)
                intervals.append((left, right, rng.randrange(20)))
            before = list(intervals)
            assert WORKERS.minimum_workers(intervals, mode=mode) == oracle(intervals)
            assert intervals == before
        counts[mode] = cases
    example = [(1, 3, 6), (2, 6, 7)]
    assert WORKERS.minimum_workers(example) == 13
    assert WORKERS.minimum_workers(example, mode="continuous_half_open") == 13
    touching = [(1, 2, 6), (2, 3, 7)]
    assert WORKERS.minimum_workers(touching) == 13
    assert WORKERS.minimum_workers(touching, mode="continuous_half_open") == 7
    invalid = [[(3, 2, 1)], [(1, 2, -1)], [(1.5, 2, 1)], [(1, 2, True)]]
    for source in invalid:
        with pytest.raises(ValueError):
            WORKERS.minimum_workers(source)
    for endpoint in (float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            WORKERS.minimum_workers([(0, endpoint, 1)], mode="continuous_half_open")
    return {"exhaustive_cases_by_endpoint_contract": counts, "seeded_cases_each_contract": 150,
            "source_example_peak": 13, "touching_inclusive_peak": 13,
            "touching_half_open_peak": 7, "invalid_cases": 7}


def matrix_oracle(source):
    # Construct the entire result from the untouched source, with no in-place markers.
    return [[0 if any(value == 0 for value in source[i])
             or any(source[k][j] == 0 for k in range(len(source))) else item
             for j, item in enumerate(row)] for i, row in enumerate(source)]


def matrix_case(source):
    expected = matrix_oracle(source)
    for function in (MATRIX.zero_with_flags, MATRIX.zero_inplace_markers):
        target = [list(row) for row in source]
        identities = [id(row) for row in target]
        assert function(target) is target
        assert target == expected
        assert [id(row) for row in target] == identities


def check_matrix_cases():
    count = 0
    for rows in range(4):
        for columns in range(4):
            for flat in itertools.product((0, 1), repeat=rows * columns):
                source = [flat[i * columns:(i + 1) * columns] for i in range(rows)]
                matrix_case(source)
                count += 1
    for flat in itertools.product((0, 1), repeat=16):
        matrix_case([flat[i * 4:(i + 1) * 4] for i in range(4)])
        count += 1
    rng = random.Random(150)
    for _ in range(300):
        rows, columns = rng.randrange(21), rng.randrange(21)
        matrix_case([[rng.choice((-5, 0, 2, 9)) for _ in range(columns)] for _ in range(rows)])
    witness = [[0, 1], [1, 1]]
    MATRIX.zero_inplace_markers(witness)
    assert witness == [[0, 0], [0, 1]]
    # Do not test idempotence: a second invocation sees newly created zeros.
    for function in (MATRIX.zero_with_flags, MATRIX.zero_inplace_markers):
        for invalid in ([[1], [2, 3]], [[1], (2,)]):
            before = repr(invalid)
            with pytest.raises(ValueError):
                function(invalid)
            assert repr(invalid) == before
    return {"exhaustive_binary_matrices": count, "seeded_matrices": 300,
            "implementations_each": 2, "original_zero_no_cascade_witness_checked": True,
            "invalid_shape_or_row_cases_each": 2}


def check_popcount_cases():
    functions = (COUNT.count_scan, COUNT.count_sparse, COUNT.count_parallel, COUNT.count_lookup)
    for value in range(256):
        expected = bin(value).count("1")
        for function in functions:
            assert function(value) == expected
        assert COUNT.BYTE_COUNTS[value] == expected
        assert expected + COUNT.count_parallel(value ^ 0xFF) == 8
    for invalid in (-1, 256, True, 1.5):
        for function in functions:
            with pytest.raises(ValueError):
                function(invalid)
    return {"all_unsigned_byte_inputs": 256, "implementations_each": 4,
            "table_entries_verified": 256, "invalid_values_each": 4,
            "python_executed": True, "c_or_hdl_compiled": False}


def check_width_reversal_cases():
    count = 0
    for width in range(13):
        for value in range(1 << width):
            expected = int(f"{value:0{width}b}"[::-1], 2) if width else 0
            actual = REVERSE.reverse_bits(value, width)
            assert actual == expected
            assert REVERSE.reverse_bits(actual, width) == value
            assert actual.bit_count() == value.bit_count()
            count += 1
    rng = random.Random(9416)
    for width in (13, 16, 31, 32, 63, 64, 65, 127):
        for _ in range(100):
            value = rng.getrandbits(width)
            assert REVERSE.reverse_bits(value, width) == int(f"{value:0{width}b}"[::-1], 2)
    assert REVERSE.reverse_bits(0b1100101, 7) == 0b1010011
    assert REVERSE.reverse_bits(1, 7) == 64
    assert REVERSE.reverse_bits(1, 8) == 128
    for value, width in ((-1, 8), (256, 8), (1, 0), (True, 1), (1, -1), (1, True)):
        with pytest.raises(ValueError):
            REVERSE.reverse_bits(value, width)
    return {"exhaustive_width0_through12_inputs": count, "seeded_wide_inputs": 800,
            "source_example_width": 7, "source_example_decimal_result": 83,
            "invalid_cases": 6, "original_byte_contract_retained": True}


def test_costume_assignment_lexicographic_objective_matches_full_product_oracle():
    assert check_costume_cases()["four_person_source_score"] == [4, 3]


def test_worker_peak_matches_direct_demand_sampling_under_both_endpoint_contracts():
    assert check_worker_cases()["source_example_peak"] == 13


def test_matrix_zeroes_derive_only_from_original_data_in_both_implementations():
    assert check_matrix_cases()["original_zero_no_cascade_witness_checked"]


def test_every_byte_popcount_method_matches_independent_text_oracle():
    assert check_popcount_cases()["implementations_each"] == 4


def test_given_width_reversal_includes_leading_zero_positions_and_zero_width():
    assert check_width_reversal_cases()["source_example_decimal_result"] == 83
