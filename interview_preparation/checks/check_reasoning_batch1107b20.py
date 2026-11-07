"""Finite independent oracles for parent reachability, byte counts and rope math."""
import importlib.util
import itertools
import json
import math
import random
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / 'solutions' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Node:
    __hash__ = None

    def __init__(self, root=False):
        self.parent = None
        self.root = root
        self.parent_calls = self.root_calls = 0

    def __eq__(self, other):
        return True  # Deliberately defeats value-based keys/comparison.

    def get_parent(self):
        self.parent_calls += 1
        return self.parent

    def is_root(self):
        self.root_calls += 1
        return self.root


def parent_check():
    candidate = load('prep_284_parent_components_batch1107b20').disconnected_nodes
    count = 0
    for n in range(1, 6):
        for mapping in itertools.product(range(-1, n), repeat=n):
            nodes = [Node(root=(i == 0)) for i in range(n)]
            for i, parent in enumerate(mapping):
                nodes[i].parent = None if parent < 0 else nodes[parent]
            before = [id(v.parent) for v in nodes]
            result = candidate(nodes)
            assert all(v.parent_calls == v.root_calls == 1 for v in nodes)
            expected = []
            for start in range(n):
                cursor, seen = start, set()
                while cursor != 0 and cursor != -1 and cursor not in seen:
                    seen.add(cursor)
                    cursor = mapping[cursor]
                if cursor != 0:
                    expected.append(nodes[start])
            assert [id(v) for v in result] == [id(v) for v in expected]
            assert [id(v.parent) for v in nodes] == before
            count += 1
    # A long chain verifies iterative traversal, not recursion-limit luck.
    chain = [Node(root=(i == 0)) for i in range(5000)]
    for i in range(1, len(chain)):
        chain[i].parent = chain[i - 1]
    assert candidate(list(reversed(chain))) == []
    invalid = [[], [Node()], [Node(True), Node(True)]]
    root = Node(True)
    invalid.append([root, root])
    child = Node(); child.parent = Node()
    invalid.append([Node(True), child])
    bad_marker = Node(); bad_marker.root = 1
    invalid.append([bad_marker])
    invalid.append([object()])
    for values in invalid:
        try:
            candidate(values)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError('invalid parent input accepted')
    return {'all_parent_maps_through_five_nodes': count, 'long_chain_nodes': 5000,
            'invalid_cases': len(invalid), 'identity_not_equality_and_one_snapshot_call': True}


def byte_check():
    candidate = load('prep_151_four_bytes_batch1107b20').count_uint32
    table = tuple(sum((i >> bit) & 1 for bit in range(8)) for i in range(256))
    rng = random.Random(15120)
    values = [*range(1 << 16), 0xffffffff, 0x80000000, 0x800001ff,
              *[1 << bit for bit in range(32)],
              *[rng.randrange(1 << 32) for _ in range(1000)]]
    for value in values:
        calls = []

        def supplied_byte_count(byte, calls=calls):
            assert type(byte) is int and 0 <= byte <= 255
            calls.append(byte)
            return table[byte]

        assert candidate(value, supplied_byte_count) == value.bit_count()
        assert calls == [(value >> shift) & 255 for shift in (0, 8, 16, 24)]
    for value in (-1, 1 << 32, True, 1.5, '3'):
        try:
            candidate(value, table.__getitem__)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid uint32 accepted')
    return {'uint32_cases': len(values), 'exhaustive_low_16_bits': 65536,
            'exactly_four_byte_operations_per_valid_call': True, 'invalid_cases': 5}


def rope_check():
    candidate = load('prep_090_two_metre_rope_batch1107b20').rope_clearance
    checked = 0
    for extra in (0, 0.01, 1, 2, 10, 100):
        for height in (0, 0.1, 0.25, 0.4, 1, 2):
            result = candidate(extra, height)
            assert math.isclose(2 * math.pi * result['gap_metres'], extra, abs_tol=1e-12)
            assert result['fits'] is (height * 2 * math.pi <= extra)
            checked += 1
    chosen = candidate()
    assert chosen['fits'] and math.isclose(chosen['gap_metres'], 1 / math.pi)
    assert not candidate(2, 0.4)['fits']
    invalid = [(-1, .25), (2, -1), (math.inf, 0), (2, math.nan), (True, .25)]
    for args in invalid:
        try:
            candidate(*args)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid length accepted')
    return {'length_height_pairs': checked, 'invalid_cases': len(invalid), **chosen,
            'scope': 'Ideal circumference algebra only; no physical rope or animal trial.'}


def main():
    result = {'status': 'passed', 'recorded_on': '2026-11-07',
              'parent_map': parent_check(), 'four_bytes': byte_check(), 'rope': rope_check(),
              'inheritance_cpp': 'Separate native compiler/harness execution required; not claimed by this Python check.'}
    (BANK / 'checks/batch1107b20-reasoning-verification.json').write_text(
        json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
