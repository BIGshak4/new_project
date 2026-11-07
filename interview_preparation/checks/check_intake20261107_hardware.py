"""Independent exhaustive/random models for the November7 hardware additions.

These checks are Python checks, not a claim that RTL was compiled or CDC closed.
"""
import importlib.util
import itertools
import json
import random
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(stem):
    path = ROOT / 'solutions' / (stem + '.py')
    spec = importlib.util.spec_from_file_location(stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dabble(value, width):
    digits = 0
    for bit in range(width - 1, -1, -1):
        for shift in (0, 4):
            if ((digits >> shift) & 15) >= 5:
                digits += 3 << shift
        digits = ((digits << 1) | ((value >> bit) & 1)) & 255
    return digits >> 4, digits & 15


def test_decimal():
    count = 0
    for x in range(16):
        product = (x << 2) + x
        assert dabble(product, 7) == divmod(5*x, 10)
        count += 1
    for x in range(64):
        valid = x <= 32
        actual = (*dabble(x, 6), True) if valid else (0, 0, False)
        expected = (*divmod(x, 10), True) if x <= 32 else (0, 0, False)
        assert actual == expected
        count += 1
    return count


def test_threshold():
    count = 0
    for width in range(1, 13):
        for word in range(1 << width):
            c = 0
            for bit in range(width):
                if (word >> bit) & 1 and c != 3:
                    c += 1
            assert (c == 3) == (sum(int(v) for v in bin(word)[2:]) > 2)
            count += 1
    return count


def test_sr():
    count = 0
    for q, s, r in itertools.product(range(2), repeat=3):
        set_expected = (q, 0, 1, 1)[2*s+r]
        reset_expected = (q, 0, 1, 0)[2*s+r]
        assert (s | (q & (1-r))) == set_expected
        assert ((1-r) & (s | q)) == reset_expected
        count += 2
    return count


def test_serial_seven():
    count = 0
    # Independent integer reconstruction supplies the result, not FSM equations.
    for length in range(1, 13):
        for word in range(1 << length):
            remainder, built, low, appended, weight = 0, 0, 0, 0, 1
            for position in range(length):
                bit = (word >> position) & 1
                remainder = (remainder + bit*weight) % 7
                weight = (weight*2) % 7
                built += bit << position
                assert remainder == built % 7
                assert (remainder == 0) == (built % 7 == 0)
                low = (2*low + bit) % 7
                appended = 2 * appended + bit
                assert low == appended % 7
                assert (low == 0) == (appended % 7 == 0)
                count += 4
    return count


def test_netlist():
    solve = load('prep_261_buffer_chain_netlist').buffer_chains
    count = 0
    # Independent DFS enumerates all paths only on these small DAGs.
    for width in range(1, 7):
        possible = [(a, b) for a in range(width) for b in range(a+1, width)]
        patterns = range(1 << len(possible)) if width <= 5 else range(800)
        for pattern in patterns:
            nodes = {str(i): 'buffer' for i in range(width)}
            nodes['sink'] = 'ff'
            edges = {name: [] for name in nodes}
            predecessors = {str(i): set() for i in range(width)}
            for bit, (a, b) in enumerate(possible):
                if (pattern >> bit) & 1:
                    edges[str(a)].append((str(b), 'wire'))
                    predecessors[str(b)].add(str(a))
            for i in range(width):
                if not edges[str(i)]:
                    edges[str(i)].append(('sink', 'data'))
            def longest(node, parents=predecessors):
                return 1 + max((longest(p, parents) for p in parents[node]), default=0)
            result = solve(nodes, edges, limit=2)
            expected_lengths = {str(i): longest(str(i)) for i in range(width)}
            assert result['longest_to_buffer'] == expected_lengths
            expected_ends = {str(i) for i in range(width)
                             if edges[str(i)] == [('sink', 'data')]
                             and expected_lengths[str(i)] > 2}
            assert {r['end'] for r in result['reports']} == expected_ends
            for report in result['reports']:
                witness = report['witness']
                assert len(witness) == report['length']
                assert all((b, 'wire') in edges[a] for a, b in itertools.pairwise(witness))
            count += 1
    nodes = {str(i): 'buffer' for i in range(12)} | {'f': 'ff'}
    edges = {str(i): [(str(i+1), 'wire')] for i in range(11)}
    edges['11'] = [('f', 'reset')]
    assert not solve(nodes, edges)['reports']
    assert len(solve(nodes, edges)['excluded_control_buffers']) == 12
    edges['11'].append(('f', 'data'))
    assert solve(nodes, edges)['reports'][0]['length'] == 12
    edges['11'] = [('0', 'wire')]
    try:
        solve(nodes, edges)
    except ValueError:
        count += 4
    else:
        raise AssertionError('Buffer cycle accepted')
    return count


def test_fifo():
    fifo_class = load('prep_264_async_fifo_model').GrayFifo
    count = 0
    fifo = fifo_class()
    assert fifo.write_edge(True, 91)
    visibility = []
    acceptances = []
    for _ in range(4):
        take, data = fifo.read_edge(True)
        visibility.append(fifo.empty)
        acceptances.append(take)
    assert visibility == [True, True, False, True]
    assert acceptances == [False, False, False, True] and data == 91
    count += 6
    rng = random.Random(1107264)
    for aw in range(1, 6):
        fifo, expected = fifo_class(aw), deque()
        sequence = 0
        for _ in range(50000):
            if rng.randrange(2):
                request = bool(rng.randrange(4))
                before = fifo.wgray
                if fifo.write_edge(request, sequence):
                    assert len(expected) < fifo.depth
                    expected.append(sequence)
                    sequence += 1
                difference = before ^ fifo.wgray
                assert difference == 0 or difference & (difference-1) == 0
            else:
                request = bool(rng.randrange(4))
                before = fifo.rgray
                take, data = fifo.read_edge(request)
                if take:
                    assert expected and data == expected.popleft()
                difference = before ^ fifo.rgray
                assert difference == 0 or difference & (difference-1) == 0
            assert 0 <= len(expected) <= fifo.depth
            count += 2
        for _ in range(4):
            fifo.read_edge(False)
        while expected:
            take, data = fifo.read_edge(True)
            assert take and data == expected.popleft()
            count += 1
        for _ in range(4):
            take, _data = fifo.read_edge(True)
            assert not take
            count += 1
    return count


if __name__ == '__main__':
    results = {name: function() for name, function in (
        ('decimal_exhaustive', test_decimal), ('threshold_exhaustive', test_threshold),
        ('sr_priority_exhaustive', test_sr), ('serial_divisible7_prefixes', test_serial_seven),
        ('netlist_independent_dag_paths', test_netlist), ('async_fifo_event_model', test_fifo))}
    payload = {'status': 'passed', 'kind': 'Python-model verification, not RTL/CDC signoff',
               'counts': results, 'total': sum(results.values())}
    (ROOT / 'checks' / 'batch1107-hardware-python-verification.json').write_text(
        json.dumps(payload, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(payload))
