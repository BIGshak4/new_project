"""Independent finite checks for mutable lists, CSV and four variants."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import itertools
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / 'solutions' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_dictionary_native():
    evidence = json.loads((BANK / 'checks/batch1101-software-native-verification.json').read_bytes())
    assert evidence['passed'] and evidence['compile_exit'] == evidence['run_exit'] == 0
    for path, digest in evidence['canonical_lf_source_sha256'].items():
        assert hashlib.sha256((BANK.parent / path).read_text('utf-8').encode()).hexdigest() == digest
    return {'passed': True, 'cases': evidence['result']['dictionary_histories'],
            'live_blocks': evidence['result']['live_blocks'],
            'scope': 'Captured strict isolated GCC C99 execution, hash-bound to the exact source/header/harness; allocation failure injection and no live blocks. This local check verifies the evidence, not a fresh native run.'}


def check_reverse():
    module = load('prep_238_reverse_linked_list')
    cases = 0
    for length in range(9):
        for values in itertools.product((-1, 0, 1), repeat=length):
            nodes = [module.Node(value) for value in values]
            for left, right in itertools.pairwise(nodes):
                left.next = right
            head = module.reverse_list(nodes[0] if nodes else None)
            current = head
            for expected in reversed(nodes):
                assert current is expected and current.value == expected.value
                current = current.next
            assert current is None
            restored = module.reverse_list(head)
            assert restored is (nodes[0] if nodes else None)
            assert [node.next for node in nodes] == nodes[1:] + ([None] if nodes else [])
            cases += 1
    return {'passed': True, 'cases': cases, 'scope': 'Exact node identities, links, values and restoration, lengths zero through eight over three values.'}


def check_csv():
    module = load('prep_239_streaming_csv')
    values = ['', 'a', 'a,b', 'a"b', 'a\r\nb', '\n', ',', '"', ' ']
    rows = [[value] for value in values] + [list(pair) for pair in itertools.product(values, repeat=2)]
    cases = chunks = 0
    for row_count in range(3):
        for expected in itertools.product(rows, repeat=row_count):
            stream = io.StringIO(newline='')
            csv.writer(stream, lineterminator='\r\n').writerows(expected)
            text = stream.getvalue()
            assert list(csv.reader(io.StringIO(text, newline=''), strict=True)) == list(expected)
            for size in [1, 2, 5, max(1, len(text))]:
                pieces = [text[i:i + size] for i in range(0, len(text), size)]
                assert list(module.iter_csv_rows(pieces)) == list(expected)
                chunks += 1
            cases += 1
    directed = {'': [], '\n': [['']], ',': [['', '']], 'a,b,': [['a', 'b', '']],
                'a\n': [['a']], '"a\nb",c\n': [['a\nb', 'c']],
                '"a\rb"': [['a\rb']], '""""': [['"']]}
    for text, expected in directed.items():
        assert module.parse_csv(text) == expected
    malformed = ['a"b', '"a"b', '"a', 'a\r', 'a\rb', '"a"\rX', '""x', '"a",b\r']
    for text in malformed:
        for cut in range(len(text) + 1):
            try:
                list(module.iter_csv_rows([text[:cut], text[cut:]]))
            except ValueError:
                pass
            else:
                raise AssertionError(('malformed accepted', text, cut))
    iterator = module.iter_csv_rows(['ok\n"unterminated'])
    assert next(iterator) == ['ok']
    try:
        next(iterator)
    except ValueError:
        pass
    else:
        raise AssertionError('later malformed record accepted')
    return {'passed': True, 'generated_records_cases': cases, 'chunked_runs': chunks,
            'directed_cases': len(directed), 'malformed_texts': len(malformed),
            'scope': 'Independently csv.writer-encoded valid records; chunk boundaries 1/2/5/whole, strict malformed cases and prefix-before-error streaming contract.'}


def check_pairs():
    module = load('prep_027_unpaired_integer_batch1101')
    cases = 0
    values = (-3, -1, 0, 2)
    for length in (1, 3, 5, 7):
        for data in itertools.product(values, repeat=length):
            odd = [value for value in values if data.count(value) % 2]
            if len(odd) == 1:
                assert module.unpaired_value(data) == odd[0]
                cases += 1
    for data in [(-2**100, 1, 1), (2**100, -7, -7), (4, 3, 2, 4, 2)]:
        assert module.unpaired_value(data) == next(v for v in data if data.count(v) % 2)
        cases += 1
    return {'passed': True, 'cases': cases, 'scope': 'All promised odd-frequency sequences through length seven over four signed values, plus wide integers and source example; source exact-pair promise is stronger.'}


def check_power():
    module = load('prep_023_power_exponent_batch1101')
    powers = {2**exponent: exponent for exponent in range(32)}
    values = list(range(65536)) + [2**31, 2**31 - 1, 2**31 + 1, 0xffffffff]
    for value in values:
        assert module.power_exponent(value) == ([True, powers[value]] if value in powers else [False, None])
    return {'passed': True, 'cases': len(values), 'scope': 'Independent explicit power table, low sixteen-bit domain and uint32 boundaries; one maps to exponent zero.'}


def check_arena():
    module = load('prep_117_int_arena_batch1101')
    cases = 0
    for capacity in range(7):
        for operations in itertools.product(range(3), repeat=7):
            pool = module.IntArena(capacity)
            allocated = {}
            for step, operation in enumerate(operations):
                if operation == 0 or not allocated:
                    before = set(allocated)
                    slot = pool.alloc()
                    assert (slot is None) == (len(allocated) == capacity)
                    if slot is not None:
                        assert slot not in before and 0 <= slot < capacity
                        allocated[slot] = -(step + 1)
                        pool.data[slot] = allocated[slot]
                else:
                    slot = min(allocated) if operation == 1 else max(allocated)
                    pool.release(slot)
                    del allocated[slot]
                free, current = set(), pool.head
                while current != -1:
                    assert 0 <= current < capacity and current not in allocated and current not in free
                    free.add(current)
                    current = pool.data[current]
                assert free | set(allocated) == set(range(capacity))
                assert all(pool.data[i] == value for i, value in allocated.items())
            cases += 1
    return {'passed': True, 'histories': cases, 'scope': 'Capacities zero through six, all three-way seven-step histories with valid frees; external oracle tracks ownership, reference does not.'}


def check_packed():
    module = load('prep_151_packed_array_popcount_batch1101')
    cases = 0
    for length in range(3):
        for values in itertools.product(range(256), repeat=length):
            data = bytes(values)
            bits = [int(bit) for value in data for bit in f'{value:08b}'[::-1]]
            for count in range(8 * length + 1):
                assert module.count_packed_ones(data, count) == sum(bits[:count])
                cases += 1
    return {'passed': True, 'cases': cases, 'scope': 'Every zero/one/two-byte input and every legal bit length; independent explicit low-first bit list ignores unused tail bits.'}


CHECKS = {'237': check_dictionary_native, '238': check_reverse, '239': check_csv, '027': check_pairs,
          '023': check_power, '117': check_arena, '151': check_packed}

if __name__ == '__main__':
    for number, function in CHECKS.items():
        result = function()
        result.update(professional_review='pending', ai_assisted=True)
        suffix = '-batch1101' if number in {'027', '023', '117', '151'} else ''
        (BANK / f'checks/prep-{number}{suffix}-verification.json').write_text(
            json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(number, json.dumps(result))
