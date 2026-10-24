"""Independent source contracts for PREP-116/117 and PREP-041 variant C."""
from __future__ import annotations

import importlib.util
import itertools
import random
from collections import deque
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PALINDROME = load("prep_116_ascii_palindrome")
POOL = load("prep_117_pool64_inband_free_list")
MISSING = load("prep_041_c_zero_based_one_missing")


def check_palindrome_cases():
    count = 0
    for length in range(8):
        for letters in itertools.product("ABab", repeat=length):
            text = "".join(letters)
            assert PALINDROME.is_ascii_palindrome(text) == (text == text[::-1])
            count += 1
    assert PALINDROME.is_ascii_palindrome("aBccBa")
    assert not PALINDROME.is_ascii_palindrome("Aa")
    for invalid in (None, b"aba", 42, True, "é", "אב", "a a", "a1a", "a-a", "a\x00a"):
        with pytest.raises(ValueError):
            PALINDROME.is_ascii_palindrome(invalid)
    assert PALINDROME.is_ascii_palindrome("a" * 10001)
    return count


def validate_pool(pool, free_stack, payloads):
    assert 0 <= pool.head <= 64
    assert pool.head.bit_length() <= 7
    seen = []  # Oracle-only membership information, never part of implementation.
    current = pool.head
    while current != 64:
        assert 0 <= current < 64 and current not in seen
        seen.append(current)
        current = pool.cells[current]
    assert seen == list(free_stack)
    assert set(seen).isdisjoint(payloads)
    assert set(seen) | payloads.keys() == set(range(64))
    for index, value in payloads.items():
        assert pool.cells[index] == value


def check_pool_cases():
    rng = random.Random(117)
    cells = [0] * 64
    pool = POOL.Pool64(cells)
    assert pool.cells is cells and POOL.Pool64.__slots__ == ("cells", "head")
    free_stack, payloads = deque(range(64)), {}
    operations = 0
    # Drain, verify the sentinel, then exercise arbitrary valid free orders.
    for _ in range(64):
        index = pool.malloc_index()
        assert index == free_stack.popleft()
        payloads[index] = (1 << 64) - 1 if index % 2 else index
        cells[index] = payloads[index]
        validate_pool(pool, free_stack, payloads)
        operations += 1
    assert pool.malloc_index() == -1 and pool.head == 64
    operations += 1
    for _ in range(10000):
        if payloads and (not free_stack or rng.randrange(2)):
            index = rng.choice(tuple(payloads))
            pool.free_index(index)
            del payloads[index]
            free_stack.appendleft(index)
        elif free_stack:
            index = pool.malloc_index()
            assert index == free_stack.popleft()
            payloads[index] = rng.getrandbits(64)
            cells[index] = payloads[index]
        else:
            assert pool.malloc_index() == -1
        validate_pool(pool, free_stack, payloads)
        operations += 1
    for invalid in (-1, 64, True, None, 1.5):
        before = cells[:], pool.head
        with pytest.raises(ValueError):
            pool.free_index(invalid)
        assert (cells, pool.head) == before
    return operations


def check_missing_cases():
    count = 0
    for n in range(8):
        for missing in range(n + 1):
            values = tuple(value for value in range(n + 1) if value != missing)
            for permutation in itertools.permutations(values):
                original = list(permutation)
                expected = next(value for value in range(n + 1) if value not in original)
                assert MISSING.missing_one_with_flags(original) == expected
                assert MISSING.missing_one_xor(original) == expected
                assert original == list(permutation)
                count += 1
    rng = random.Random(41)
    for _ in range(400):
        n = rng.randrange(1, 2001)
        absent = rng.randrange(n + 1)
        values = [value for value in range(n + 1) if value != absent]
        rng.shuffle(values)
        assert MISSING.missing_one_xor(values) == absent
        assert MISSING.missing_one_with_flags(values) == absent
    return count


def test_ascii_letter_palindromes_match_independent_reverse_oracle():
    assert check_palindrome_cases() == 21845


def test_free_list_uses_free_payload_links_and_preserves_every_allocated_payload():
    assert check_pool_cases() == 10065


def test_zero_based_one_missing_flags_and_xor_match_exhaustive_permutations():
    assert check_missing_cases() == 46233
