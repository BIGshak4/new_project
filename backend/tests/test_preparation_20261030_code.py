"""Independent oracles for four manually sourced software questions."""
from __future__ import annotations

import functools
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


SEARCH = load("prep_137_first_equal_sorted")
BINARY = load("prep_138_unsigned_binary_model")
CYCLE = load("prep_141_floyd_cycle")
MINMAX = load("prep_142_pairwise_minmax")


class ReadCounter:
    def __init__(self, source):
        self.source, self.reads = source, 0

    def __len__(self):
        return len(self.source)

    def __getitem__(self, index):
        assert type(index) is int and 0 <= index < len(self.source)
        self.reads += 1
        return self.source[index]


def check_search_cases():
    count = 0
    for length in range(10):
        for source in itertools.combinations_with_replacement((-2, 0, 1, 3), length):
            for target in range(-3, 5):
                expected = next((i for i, value in enumerate(source) if value == target), -1)
                wrapped = ReadCounter(source)
                assert SEARCH.first_equal(wrapped, target) == expected
                assert wrapped.reads <= length.bit_length() + 1
                count += 1
    rng = random.Random(137)
    for _ in range(1000):
        source = sorted(rng.randrange(-100, 101) for _ in range(rng.randrange(1001)))
        before, target = list(source), rng.randrange(-105, 106)
        expected = next((i for i, value in enumerate(source) if value == target), -1)
        assert SEARCH.first_equal(source, target) == expected
        assert source == before
    assert SEARCH.first_equal([1, 2, 2, 2, 3, 3, 3, 4], 3) == 4
    return {"exhaustive_sorted_array_target_cases": count, "seeded_arrays": 1000,
            "logarithmic_element_access_bound_checked": True, "source_example_index": 4}


def binary_case(value, width):
    expected = format(value, "b").encode("ascii")
    successful = 0
    for capacity in (0, len(expected), len(expected) + 1, len(expected) + 3):
        out = bytearray([0xA5] * (len(expected) + 5))
        before = bytes(out)
        result = BINARY.unsigned_to_binary(value, out, capacity, width=width)
        assert result == (capacity > len(expected))
        if result:
            assert bytes(out[:len(expected)]) == expected
            assert out[len(expected)] == 0
            assert bytes(out[len(expected) + 1:]) == before[len(expected) + 1:]
            successful += 1
        else:
            assert bytes(out) == before
    assert not BINARY.unsigned_to_binary(value, None, len(expected) + 1, width=width)
    return successful


def check_binary_cases():
    successes = sum(binary_case(value, 32) for value in range(1 << 16))
    boundaries = {(0, 1), (1, 1)}
    for width in (8, 16, 32, 64, 127):
        boundaries.add(((1 << width) - 1, width))
        for bit in range(width):
            for delta in (-1, 0, 1):
                value = (1 << bit) + delta
                if 0 <= value < 1 << width:
                    boundaries.add((value, width))
    for value, width in sorted(boundaries):
        successes += binary_case(value, width)
    for invalid in (-1, 1 << 32, True, 1.5):
        with pytest.raises(ValueError):
            BINARY.unsigned_to_binary(invalid, bytearray(40), 40)
    return {"all_uint16_values_in_uint32_model": 65536, "wide_boundary_cases": len(boundaries),
            "successful_buffer_writes": successes, "capacity_cases_per_value": 4,
            "null_pointer_cases_per_value": 1, "c_compiled": False,
            "scope": "Python equivalent executed; actual C source supplied but not compiled."}


def oracle_cycle_entry(head):
    seen = set()
    while head is not None and id(head) not in seen:
        seen.add(id(head))
        head = head.next
    return head


def check_cycle_cases():
    configs = 0
    for n in range(6):
        for targets in itertools.product(range(-1, n), repeat=n):
            nodes = [CYCLE.Node(7) for _ in range(n)]
            for node, target in zip(nodes, targets, strict=True):
                node.next = None if target == -1 else nodes[target]
            before = tuple(node.next for node in nodes)
            for start in range(-1, n):
                head = None if start == -1 else nodes[start]
                expected = oracle_cycle_entry(head)
                assert CYCLE.has_cycle(head) == (expected is not None)
                assert CYCLE.cycle_entry(head) is expected
                assert tuple(node.next for node in nodes) == before
                configs += 1
    lasso_cases = 0
    max_ratio = 0
    class CountedNode:
        reads = 0

        def __init__(self):
            self.following = None

        @property
        def next(self):
            CountedNode.reads += 1
            return self.following

    for n in range(1, 65):
        for target in range(-1, n):
            nodes = [CountedNode() for _ in range(n)]
            for i in range(n - 1):
                nodes[i].following = nodes[i + 1]
            nodes[-1].following = None if target == -1 else nodes[target]
            CountedNode.reads = 0
            expected = None if target == -1 else nodes[target]
            assert CYCLE.cycle_entry(nodes[0]) is expected
            assert CountedNode.reads <= 5 * n + 2
            max_ratio = max(max_ratio, CountedNode.reads / n)
            lasso_cases += 1
    return {"all_small_functional_graph_and_head_cases": configs,
            "lasso_length1_through64_cases": lasso_cases,
            "next_access_bound": "at most 5*n+2", "largest_observed_next_reads_per_node": max_ratio,
            "equal_payloads_use_identity": True, "input_links_preserved": True}


def count_minmax(values):
    count, graph = 0, []

    def less(left, right):
        nonlocal count
        count += 1
        graph.append((left, right) if left < right else (right, left))
        return left < right
    observed = MINMAX.minmax_pairwise(values, less)
    assert observed == (min(values), max(values))
    assert count == (3 * len(values) + 1) // 2 - 2
    # With distinct values, the actual comparison graph certifies both extrema.
    if len(set(values)) == len(values):
        reached, frontier = {observed[0]}, [observed[0]]
        while frontier:
            current = frontier.pop()
            for small, large in graph:
                if small == current and large not in reached:
                    reached.add(large)
                    frontier.append(large)
        assert reached == set(values)
        reached, frontier = {observed[1]}, [observed[1]]
        while frontier:
            current = frontier.pop()
            for small, large in graph:
                if large == current and small not in reached:
                    reached.add(small)
                    frontier.append(small)
        assert reached == set(values)
    return count


def optimal_comparison_depth(n):
    """Independent minimax decision-tree search over every distinct total order.

    Each world lists labels from low to high. Query answers partition worlds.
    Leaf is valid only when all worlds agree on both extreme labels.
    Used only through n=4; the general lower bound is the written adversary proof.
    """
    worlds = tuple(itertools.permutations(range(n)))
    positions = [{label: position for position, label in enumerate(world)} for world in worlds]
    queries = tuple(itertools.combinations(range(n), 2))

    @functools.lru_cache(None)
    def solve(indices):
        answers = {(worlds[i][0], worlds[i][-1]) for i in indices}
        if len(answers) <= 1:
            return 0
        best = 2 * n
        for left, right in queries:
            yes = tuple(i for i in indices if positions[i][left] < positions[i][right])
            no = tuple(i for i in indices if positions[i][left] > positions[i][right])
            if not yes or not no:
                continue
            best = min(best, 1 + max(solve(yes), solve(no)))
        return best
    return solve(tuple(range(len(worlds))))


def check_minmax_cases():
    permutations = duplicates = 0
    for n in range(1, 9):
        for values in itertools.permutations(range(n)):
            count_minmax(values)
            permutations += 1
    for n in range(1, 8):
        for values in itertools.product((-1, 0, 1), repeat=n):
            count_minmax(values)
            duplicates += 1
    rng = random.Random(142)
    for _ in range(300):
        values = [rng.randrange(-100, 101) for _ in range(rng.randrange(1, 1001))]
        count_minmax(values)
    optima = [optimal_comparison_depth(n) for n in range(1, 5)]
    assert optima == [0, 1, 3, 4]
    with pytest.raises(ValueError):
        MINMAX.minmax_pairwise([])
    return {"all_distinct_permutations_through_n8": permutations,
            "duplicate_arrays_through_n7": duplicates, "seeded_arrays": 300,
            "independent_optimal_decision_tree_depths_n1_to4": optima,
            "exact_comparison_formula": "ceil(3*n/2)-2", "empty_rejected": True}


def test_first_equal_matches_linear_oracle_and_logarithmic_read_bound():
    assert check_search_cases()["source_example_index"] == 4


def test_unsigned_binary_python_equivalent_buffers_zero_and_word_boundaries():
    assert check_binary_cases()["all_uint16_values_in_uint32_model"] == 65536


def test_floyd_uses_node_identity_and_matches_visited_set_without_mutation():
    assert check_cycle_cases()["equal_payloads_use_identity"]


def test_pairwise_minmax_counts_matches_oracle_and_small_optimal_decision_trees():
    assert check_minmax_cases()["exact_comparison_formula"] == "ceil(3*n/2)-2"
