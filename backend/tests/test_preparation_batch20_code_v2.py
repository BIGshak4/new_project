"""Independent oracles for this intake's five software records."""
from __future__ import annotations

import importlib.util
import itertools
import random
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STACK = load("prep_131_min_stack")
DELETE = load("prep_135_delete_below_threshold")
MIRROR = load("prep_094_c_mirror_models")
MISSING = load("prep_041_d_all_missing_with_repeats")
MERGE = load("prep_098_inplace_reserved_capacity")


def stack_action(stack, oracle, operation):
    if type(operation) is int:
        stack.push(operation)
        oracle.append(operation)
    elif not oracle:
        with pytest.raises(IndexError):
            getattr(stack, operation)()
    elif operation == "pop":
        assert stack.pop() == oracle.pop()
    elif operation == "top":
        assert stack.top() == oracle[-1]
    else:
        assert stack.find_min() == min(oracle)
    assert len(stack) == len(oracle)
    if oracle:
        assert (stack.top(), stack.find_min()) == (oracle[-1], min(oracle))


def check_stack_cases():
    sequences = 0
    for length in range(7):
        for operations in itertools.product((1, 2, "pop", "top", "find_min"), repeat=length):
            stack, oracle = STACK.MinStack(), []
            for operation in operations:
                stack_action(stack, oracle, operation)
            sequences += 1
    stack, oracle, rng = STACK.MinStack(), [], random.Random(131)
    for _ in range(10000):
        operation = rng.randrange(-50, 51) if rng.randrange(2) else rng.choice(("pop", "top", "find_min"))
        stack_action(stack, oracle, operation)
    for invalid in (True, None, "1", 1.5):
        before = len(stack), stack._head
        with pytest.raises(ValueError):
            stack.push(invalid)
        assert before == (len(stack), stack._head)
    return {"exhaustive_sequences": sequences, "seeded_operations": 10000, "invalid_pushes": 4}


def check_delete_cases():
    arrays = []
    for length in range(9):
        arrays.extend(itertools.product((1, 18, 19, 20), repeat=length))
    rng = random.Random(135)
    arrays += [tuple(rng.randrange(1, 101) for _ in range(100)) for _ in range(200)]
    shifted = []
    for source in arrays:
        expected = [x for x in source if x >= 19]
        for function in (DELETE.delete_below_backward, DELETE.compact_then_delete_tail):
            values, indices = list(source), []
            def delete(index, values=values, indices=indices):
                assert 0 <= index < len(values)
                indices.append(index)
                values.pop(index)
            assert function(values, delete) is values
            assert values == expected
            assert len(indices) == len(source) - len(expected)
            assert all(a > b for a, b in itertools.pairwise(indices))
    # A shifting-array cost witness: kept suffix is moved by every prefix delete.
    for function in (DELETE.delete_below_backward, DELETE.compact_then_delete_tail):
        values, moves = [1] * 50 + [19] * 50, [0]
        def delete(index, values=values, moves=moves):
            moves[0] += len(values) - index - 1
            values.pop(index)
        function(values, delete)
        shifted.append(moves[0])
        assert values == [19] * 50
    assert shifted == [2500, 0]
    return {"exhaustive_arrays": sum(4**n for n in range(9)), "seeded_length100_arrays": 200,
            "implementations_each": 2, "backward_shift_witness": 2500, "compaction_tail_shifts": 0}


def check_mirror_cases():
    for value in range(256):
        expected = int(f"{value:08b}"[::-1], 2)
        assert MIRROR.reverse_loop(value) == MIRROR.reverse_masks(value) == expected
        assert MIRROR.reverse_masks(expected) == value
        assert expected.bit_count() == value.bit_count()
    for value in (-1, 256, True, 1.5):
        for function in (MIRROR.reverse_loop, MIRROR.reverse_masks):
            with pytest.raises(ValueError):
                function(value)
    return {"all_byte_inputs": 256, "python_models_each": 2, "c_compiled": False,
            "c_scope": "C source supplied; no clang, gcc, cl or g++ command discovered on PATH."}


def check_missing_cases():
    cases = 0
    for n in range(1, 8):
        for source in itertools.product(range(n + 1), repeat=n - 1):
            expected = [value for value in range(1, n + 1) if value not in source]
            readonly, mutable = list(source), list(source)
            assert MISSING.missing_all_flags(readonly, n) == expected
            assert readonly == list(source)
            assert MISSING.missing_all_inplace(mutable, n) == expected
            assert sorted(mutable) == sorted(source)
            cases += 1
    rng = random.Random(413)
    for _ in range(300):
        n = rng.randrange(1, 101)
        source = [rng.randrange(n + 1) for _ in range(n - 1)]
        expected = [value for value in range(1, n + 1) if value not in source]
        assert MISSING.missing_all_flags(source, n) == expected
        assert MISSING.missing_all_inplace(list(source), n) == expected
    assert MISSING.missing_all_flags([], 0) == []
    assert MISSING.missing_all_flags([0, 0, 3, 3, 3], 3) == [1, 2]
    assert MISSING.missing_all_inplace([0, 0, 0], 4) == [1, 2, 3, 4]
    for invalid in ([4, 0], [-1, 2], [True, 0]):
        before = list(invalid)
        with pytest.raises(ValueError):
            MISSING.missing_all_inplace(invalid, 3)
        assert invalid == before
    return {"exhaustive_n_minus_one_arrays": cases, "seeded_arrays": 300,
            "extra_general_length_cases": 2, "atomic_invalid_cases": 3}


def check_merge_cases():
    arrays = [word for n in range(6) for word in itertools.combinations_with_replacement((-2, 0, 3), n)]
    count = 0
    for left, right in itertools.product(arrays, repeat=2):
        a, b = list(left), list(right) + [0] * len(left)
        assert MERGE.merge_into_right(a, b, len(right)) is b
        assert b == sorted(left + right) and a == list(left)
        count += 1
    rng = random.Random(9815)
    for _ in range(200):
        a = sorted(rng.randrange(-100, 101) for _ in range(rng.randrange(101)))
        right = sorted(rng.randrange(-100, 101) for _ in range(rng.randrange(101)))
        before = list(a)
        b = right + [0] * len(a)
        MERGE.merge_into_right(a, b, len(right))
        assert a == before and b == sorted(before + right)
    same = []
    with pytest.raises(ValueError):
        MERGE.merge_into_right(same, same, 0)
    return {"exhaustive_sorted_pairs": count, "seeded_pairs": 200, "same_object_rejected": True}


def test_min_stack_matches_list_min_oracle_with_duplicates_and_empty_operations():
    assert check_stack_cases()["exhaustive_sequences"] == 19531


def test_delete_variants_match_stable_filter_and_expose_actual_shift_cost():
    assert check_delete_cases()["exhaustive_arrays"] == 87381


def test_python_models_of_c_mirror_match_all_256_independent_bitstring_reversals():
    assert check_mirror_cases()["all_byte_inputs"] == 256


def test_missing_all_variants_match_membership_oracle_without_invented_zero_output():
    assert check_missing_cases()["seeded_arrays"] == 300


def test_inplace_merge_preserves_a_and_target_identity_with_real_zero_values():
    assert check_merge_cases()["exhaustive_sorted_pairs"] == 3136
