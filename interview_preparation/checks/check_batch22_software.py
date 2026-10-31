"""Executable, independent finite oracles for six new software questions.

All Python sources execute locally. C source is compiled separately when a
compiler is available; this script never labels a Python model as compiled C.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'interview_preparation'


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / 'solutions' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def finish(ident, cases, detail):
    return {'question_id': ident, 'passed': True, 'cases': cases, 'detail': detail,
            'python_executed': True, 'c_compiled_locally': False,
            'professional_review': 'pending', 'ai_assisted': True}


def check_224():
    module = load('prep_224_merge_k_sorted_linked_lists')
    sequences = [list(a) for n in range(4) for a in itertools.combinations_with_replacement((-1, 0, 1), n)]
    cases = 0
    for k in range(4):
        for lists in itertools.product(sequences, repeat=k):
            heads, labelled = [], []
            for list_index, values in enumerate(lists):
                head = None
                for position in reversed(range(len(values))):
                    head = module.Node(values[position], head)
                    labelled.append((values[position], list_index, position, head))
                heads.append(head)
            expected = [item[-1] for item in sorted(labelled, key=lambda item: item[:3])]
            node, actual, seen = module.merge_k_lists(heads), [], set()
            while node is not None:
                assert id(node) not in seen
                seen.add(id(node))
                actual.append(node)
                node = node.next
            assert actual == expected
            cases += 1
    return finish('PREP-224', cases, 'Every sorted list of length0..3 over{-1,0,1}, combined atK0..3; compares exact node identity, source-index tie stability, multiplicity and acyclic termination against independently sorted tagged records.')


def check_225():
    function = load('prep_225_word_list_mode').most_frequent_word
    cases = 0
    for length in range(7):
        for words in itertools.product(('a', 'b', 'A', ''), repeat=length):
            values = list(words)
            best = max(values, key=values.count) if values else None
            expected = [best, values.count(best)] if values else None
            assert function(values) == expected
            assert values == list(words)
            cases += 1
    assert function(['red', 'blue', 'blue', 'red']) == ['red', 2]
    assert function(['Hello', 'hello', 'Hello']) == ['Hello', 2]
    return finish('PREP-225', cases + 2, 'Exhaustive lists through length6 over four exact string tokens, plus case-sensitive and first-appearance tie examples; input remains unchanged.')


def check_226():
    function = load('prep_226_ascii_word_anagrams').are_anagrams
    words = [''.join(chars) for n in range(5) for chars in itertools.product('aAb', repeat=n)]
    cases = 0
    for left, right in itertools.product(words, repeat=2):
        assert function(left, right) == (sorted(left) == sorted(right))
        cases += 1
    for invalid in ('a!', 'a b', 'é', '7'):
        try:
            function(invalid, 'a')
        except ValueError:
            pass
        else:
            raise AssertionError('invalid alphabet accepted')
        cases += 1
    return finish('PREP-226', cases, 'All pairs of121words overa/A/b through length4 matched independent sorted-character equality; invalid alphabet rejection checked separately.')


def check_228():
    function = load('prep_228_stack_applications').stack_trace
    operations = [('push', 'A'), ('push', 'B'), ('pop', None), ('push', 'C'), ('pop', None), ('pop', None)]
    assert function(operations) == {'removed': ['B', 'C', 'A'], 'remaining_bottom_to_top': []}
    assert function([]) == {'removed': [], 'remaining_bottom_to_top': []}
    for operations in ([('pop', None)], [('push', 1), ('pop', None), ('pop', None)]):
        try:
            function(operations)
        except IndexError:
            pass
        else:
            raise AssertionError('underflow not reported')
    return finish('PREP-228', 4, 'Concrete LIFO operation traces and underflow; conceptual uses and ABI distinctions require explanatory review, not an execution score.')


def check_229():
    function = load('prep_229_stable_zero_compaction').move_zeroes
    cases = 0
    for length in range(9):
        for values in itertools.product((-1, 0, 1), repeat=length):
            data = list(values)
            expected = [x for x in values if x != 0] + [0] * values.count(0)
            assert function(data) is data
            assert data == expected and len(data) == len(values)
            assert function(data) is data and data == expected
            cases += 1
    source = [1, 0, 9, 0, 3, 4, 5, 1]
    assert function(source) == [1, 9, 3, 4, 5, 1, 0, 0]
    return finish('PREP-229', cases + 1, 'All arrays over{-1,0,1} through length8 plus supplied duplicate-one example; identity, size, stable order, multiplicity and idempotence verified.')


def check_230():
    module = load('prep_230_fifo_requests_model')
    cases = 0
    for capacity in range(1, 5):
        for length in range(7):
            for codes in itertools.product(range(4), repeat=length):
                fifo, expected = module.RequestFifo(capacity), deque()
                reads = writes = 0
                for step, code in enumerate(codes):
                    write, read, value = bool(code & 2), bool(code & 1), step % 3 - 1
                    wrote = write and len(expected) < capacity
                    if wrote:
                        expected.append(value)
                        writes += 1
                    accepted_read = read and bool(expected)
                    removed = expected.popleft() if accepted_read else None
                    reads += accepted_read
                    assert fifo.step(write, value, read) == {'wrote': wrote, 'read': accepted_read, 'value': removed}
                    assert fifo.contents() == list(expected)
                    assert fifo.read_head == reads % capacity and fifo.write_head == writes % capacity
                    assert fifo.is_full == (len(expected) == capacity)
                    assert fifo.is_empty == (not expected)
                cases += 1
    return finish('PREP-230', cases, 'All four request combinations over histories through length6, capacities1..4; independent deque write-then-read oracle verifies accept/reject, wrap, heads, flags and logical contents. C compilation is a separate harness result.')


def check_094():
    function = load('prep_094_significant_bits_batch22').reverse_significant
    for value in range(65536):
        expected = int(format(value, 'b')[::-1], 2)
        assert function(value) == expected
    for value in (0x80000000, 0xffffffff, 0x80000001):
        assert function(value) == int(format(value, 'b')[::-1], 2)
    assert function(13) == 11 and int(f'{13:08b}'[::-1], 2) == 176
    return finish('PREP-094', 65539, 'Every unsigned16-bit value plus32-bit boundaries; significant-width reversal is checked separately from fixed-eight-bit reversal13->176.')


def check_160():
    module = load('prep_160_uppercase_counting_batch22')
    cases = 0
    for length in range(9):
        for letters in itertools.product('AMZ', repeat=length):
            data = list(letters)
            assert module.sort_uppercase(data) is data
            assert data == sorted(letters)
            cases += 1
    data = list(('ZYXWVUTSRQPONMLKJIHGFEDCBA' * 39)[:1000])
    expected = sorted(data)
    assert module.sort_uppercase(data) == expected
    invalid = list('ZA!B')
    try:
        module.sort_uppercase(invalid)
    except ValueError:
        assert invalid == list('ZA!B')
    else:
        raise AssertionError('invalid alphabet accepted')
    return finish('PREP-160', cases + 2, 'All AMZ strings through length8, a1000-character uppercase case and invalid-input nonmutation; compared with independent comparison sort. Does not replace the original external-memory model.')


CHECKS = {'224': check_224, '225': check_225, '226': check_226, '228': check_228,
          '229': check_229, '230': check_230, '094': check_094, '160': check_160}


if __name__ == '__main__':
    for number, check in CHECKS.items():
        result = check()
        suffix = '-software-batch22' if number in ('094', '160') else ''
        (BANK / f'checks/prep-{number}{suffix}-verification.json').write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f"PREP-{number}: {result['cases']} cases passed")
