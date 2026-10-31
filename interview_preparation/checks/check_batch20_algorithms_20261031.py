"""Independent finite Python oracles; C compilation is reported separately.

Run with --write to persist only Python reports. This script does not mistake
the Python checks for execution of the opaque C linked-list implementation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import itertools
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
SOLUTIONS = HERE.parent / 'solutions'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SOLUTIONS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReadCounter:
    def __init__(self, values):
        self.values = values
        self.reads = 0

    def __len__(self):
        return len(self.values)

    def __getitem__(self, index):
        assert isinstance(index, int) and 0 <= index < len(self.values)
        self.reads += 1
        return self.values[index]


def check_damaged_triples():
    model = load('prep_210_damaged_triple_groups')
    exhaustive = source_length = 0
    largest_read_count = 0

    def check(groups, damaged):
        nonlocal largest_read_count
        values = [value for i, value in enumerate(groups)
                  for _ in range(1 if i == damaged else 3)]
        before = list(values)
        # Independent global frequency oracle, without run boundaries or indices.
        counts = Counter(values)
        candidates = [value for value, count in counts.items() if count % 3 == 1]
        assert candidates == [groups[damaged]]
        assert all(count % 3 in (0, 1) for count in counts.values())
        wrapped = ReadCounter(values)
        assert model.damaged_value(wrapped) == candidates[0]
        assert values == before
        assert wrapped.reads <= 2 * len(values) - 1
        largest_read_count = max(largest_read_count, wrapped.reads)

    for group_count in range(1, 7):
        for groups in itertools.product((0, 1, 2), repeat=group_count):
            for damaged in range(group_count):
                check(groups, damaged)
                exhaustive += 1
    # Source size is 255 before deletion and 253 afterwards. Include coalesced
    # adjacent repeats and recurring values separated by other-valued groups.
    for groups in ([7] * 85, [i % 2 for i in range(85)], [(i * 7) % 11 - 5 for i in range(85)]):
        for damaged in range(85):
            check(groups, damaged)
            source_length += 1
    assert exhaustive == 6015 and source_length == 255
    return {'question_id': 'PREP-210', 'passed': True,
            'exhaustive_group_damage_configurations': exhaustive,
            'source_length_253_cases': source_length,
            'cases': exhaustive + source_length,
            'oracle': 'Global Counter residues modulo three, independent of equality-run scanning',
            'element_read_bound': 'at most 2*n-1',
            'largest_observed_element_reads': largest_read_count,
            'scope': 'Every 1..6-group sequence over {0,1,2}, every damaged group; three 85-group families at every damage position. Promise inputs only; finite testing is not the general proof.',
            'professional_review': 'pending'}


def check_top_two_and_mode():
    model = load('prep_211_top_two_and_mode')
    exhaustive = seeded = boundaries = 0

    def check(source):
        before = list(source)
        ordered = sorted(set(source), reverse=True)
        expected_top = tuple((value, source.count(value)) for value in ordered[:2])
        expected_top += (None,) * (2 - len(expected_top))
        # Sort all value/count candidates with an explicit secondary key;
        # this oracle does not share the proposed online best-update rule.
        frequencies = [(source.count(value), value) for value in set(source)]
        expected_mode = None
        if frequencies:
            count, value = min(frequencies, key=lambda item: (-item[0], item[1]))
            expected_mode = (value, count)
        assert model.top_two_distinct(source) == expected_top
        assert model.mode_with_count(source) == expected_mode
        assert source == before

    for length in range(9):
        for source in itertools.product((-2, 0, 3), repeat=length):
            check(list(source))
            exhaustive += 1
    rng = random.Random(20261031211)
    for _ in range(200):
        check([rng.randrange(-17, 18) for _ in range(rng.randrange(201))])
        seeded += 1
    for source in ([], [5, 5, 4, 4, 2], [0, 0, 0], [-4, -2, -4, -2],
                   [2**400, -(2**401), 2**400, -(2**401), 17]):
        check(source)
        boundaries += 1
    assert exhaustive == 9841
    return {'question_id': 'PREP-211', 'passed': True,
            'exhaustive_arrays': exhaustive, 'seeded_arrays': seeded,
            'boundary_arrays': boundaries, 'cases': exhaustive + seeded + boundaries,
            'oracle': 'Sorted distinct values and independent list.count frequencies with explicit smallest-value mode tie',
            'scope': 'All arrays over {-2,0,3} of length0..8, 200 reproducible samples, empty/single distinct/ties/negative/wide integer boundaries. Python algorithms executed; no claim of worst-case constant-time hashing.',
            'professional_review': 'pending'}


CHECKS = {'PREP-210': check_damaged_triples, 'PREP-211': check_top_two_and_mode}


def amalgamate_c_harness():
    """Expand exactly the two project-local includes for a single-file runner."""
    header = (SOLUTIONS / 'prep_212_linked_list_adt.h').read_text('utf-8')
    implementation = (SOLUTIONS / 'prep_212_linked_list_adt.c').read_text('utf-8')
    harness = (HERE / 'prep_212_linked_list_adt_test.c').read_text('utf-8')
    implementation = implementation.replace('#include "prep_212_linked_list_adt.h"', header)
    harness = harness.replace('#include "../solutions/prep_212_linked_list_adt.c"', implementation)
    return '/* Generated exact include expansion of public header, implementation and harness. */\n' + harness


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    results = [check() for check in CHECKS.values()]
    if args.write:
        (HERE / 'prep_212_linked_list_adt_amalgamated.c').write_text(amalgamate_c_harness(), encoding='utf-8')
        for result in results:
            (HERE / (result['question_id'].lower() + '-verification.json')).write_text(
                json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
