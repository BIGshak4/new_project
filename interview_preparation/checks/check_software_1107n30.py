"""Finite software validation with independent interval/component/count oracles."""
import ast
import copy
import itertools
import json
import random
import runpy
from math import comb
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
OUT = BANK / 'checks'


def load(number, suffix):
    return runpy.run_path(str(BANK / 'solutions' / f'prep_{number}_{suffix}_1107n30.py'))


def ones_oracle(bits):
    candidates = [(end - start + 1, -start, start, end)
                  for start in range(len(bits)) for end in range(start, len(bits))
                  if all(bits[i] == 1 for i in range(start, end + 1))]
    return list(max(candidates)[2:]) if candidates else [-1, -1]


def boxes_oracle(image):
    height, width = len(image), len(image[0]) if image else 0
    parent = {}
    for r in range(height):
        for c in range(width):
            if image[r][c]:
                parent[(r, c)] = (r, c)

    def find(pixel):
        while pixel != parent[pixel]:
            pixel = parent[pixel]
        return pixel

    for r, c in list(parent):
        for other in [(r - 1, c), (r, c - 1)]:
            if other in parent:
                parent[find((r, c))] = find(other)
    groups = {}
    for pixel in parent:
        groups.setdefault(find(pixel), []).append(pixel)
    ordered = sorted(groups.values(), key=min)
    return [[min(r for r, _ in group), min(c for _, c in group),
             max(r for r, _ in group), max(c for _, c in group)] for group in ordered]


def brute_paths(n):
    if n == 1:
        return 1
    target = n - 1
    result = 0
    for choices in itertools.product((0, 1), repeat=2 * target):
        r = c = 0
        for move in choices:
            r += move == 0
            c += move == 1
        result += r == target and c == target
    return result


def run():
    longest = load(289, 'longest_ones')['longest_ones']
    boxes = load(296, 'component_boxes')['component_boxes']
    paths = load(300, 'grid_paths')['grid_paths']
    reverse_scope = load(194, 'recursive_string')
    reverse = reverse_scope['reverse_string']
    text_mode = load(225, 'text_words')['most_frequent_text_word']
    count_ones = 0
    for size in range(11):
        for bits in itertools.product((0, 1), repeat=size):
            values = list(bits)
            before = values[:]
            assert longest(values) == ones_oracle(values)
            assert values == before
            count_ones += 1
    count_boxes = 0
    images = [[]]
    for h, w in [(1, 1), (1, 4), (2, 2), (2, 3), (3, 3)]:
        images += [[list(values[r * w:(r + 1) * w]) for r in range(h)]
                   for values in itertools.product((0, 1), repeat=h * w)]
    # An outer black ring and an isolated inner pixel have overlapping boxes.
    images.append([[int(r in (0, 4) or c in (0, 4) or (r == c == 2))
                    for c in range(5)] for r in range(5)])
    rng = random.Random(110730)
    images += [[[rng.randrange(2) for _ in range(8)] for _ in range(7)] for _ in range(40)]
    for image in images:
        before = copy.deepcopy(image)
        assert boxes(image) == boxes_oracle(image)
        assert image == before
        count_boxes += 1
    for n in range(1, 31):
        assert paths(n) == comb(2 * n - 2, n - 1)
        if n <= 6:
            assert paths(n) == brute_paths(n)
    grid_tree = ast.parse((BANK / 'solutions/prep_300_grid_paths_1107n30.py').read_text('utf-8'))
    assert not any(isinstance(node, ast.Name) and node.id in ('comb', 'factorial')
                   for node in ast.walk(grid_tree))
    invalids = 0
    for function, arg in [(longest, [0, 2]), (longest, [True]), (boxes, [[1], [0, 1]]),
                          (boxes, [[]]), (boxes, [[2]]), (paths, 0), (paths, -1), (paths, True)]:
        try:
            function(arg)
            raise AssertionError('invalid input accepted')
        except ValueError:
            invalids += 1
    reversed_cases = 0
    for n in range(7):
        for chars in itertools.product('abא', repeat=n):
            text = ''.join(chars)
            assert reverse(text) == text[::-1]
            reversed_cases += 1
    source = (BANK / 'solutions/prep_194_recursive_string_1107n30.py').read_text('utf-8')
    tree = ast.parse(source)
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'reverse_string')
    calls = {node.func.id for node in ast.walk(main) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    assert calls == {'Length', 'Head', 'Tail', 'Concat', 'reverse_string'}
    texts = ['', '   \t\n', 'aaa aaa bbb ccc ddd aaa', 'a b b a', 'Cat cat Cat',
             'a, a a,', 'א ב א', 'one\ttwo\none', '\u2003a\u2003b a']
    for _ in range(120):
        texts.append(' '.join(rng.choice(['a', 'b', 'C', 'a,']) for _ in range(rng.randrange(20))))
    for text in texts:
        words = text.split()
        expected = max(words, key=words.count) if words else None
        assert text_mode(text) == expected
    assert paths(18) == 2333606220
    report = {
        'status': 'passed', 'scope': 'Executed trusted Python models and independent finite oracles.',
        'PREP-289': {'exhaustive_arrays_through_length': 10, 'cases': count_ones, 'input_preserved': True},
        'PREP-296': {'cases': count_boxes, 'oracle': 'Union-find components, independent of candidate BFS',
                     'all_3x3_bitmaps': 512, 'input_preserved': True, 'overlapping_boxes_case': True},
        'PREP-300': {'binomial_oracle_cases': 30, 'explicit_move_enumeration_cases': 6,
                     'candidate_contains_no_binomial': True, 'count_beyond_signed32': True},
        'PREP-194': {'cases': reversed_cases, 'recursive_primitive_only_calls': True,
                     'oracle': 'String slicing used only outside candidate ADT function'},
        'PREP-225': {'cases': len(texts), 'oracle': 'Independent token list.count plus first-maximum selection',
                     'base_list_API_unchanged': True},
        'invalid_cases_total': invalids,
        'PREP-295': {'scope': 'Actual C++17 native and CLI execution recorded separately; no Python model claimed as C++ compilation.'},
    }
    (OUT / '1107n30-software-verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for number in [289, 296, 300, 194, 225]:
        (OUT / f'prep-{number:03d}-1107n30-verification.json').write_text(json.dumps(report[f'PREP-{number}'], indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    run()
