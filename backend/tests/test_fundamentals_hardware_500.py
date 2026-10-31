"""Independent truth-table, prefix and event replays for all 250 new cases.

The test oracle deliberately does not call the author's answer model. Physical
cases assert the declared threshold/pass-device teaching model only, not SPICE.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import math
import re
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / 'apps/web/src/content'
SHARDS = ROOT / 'backend/seeds/duel_quiz_batches'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


CARDS = read(CONTENT / 'fundamentals-hardware-500.json')
QUIZ = read(SHARDS / 'hardware_500.json')
CHECKS = read(SHARDS / 'hardware_500.checks.json')
BY_KEY = {q['key']: q for q in QUIZ}


def oracle(n, p):
    """Enumerate values or replay events rather than consulting answer indices."""
    if n == 201:
        bits = list(f"{p['x']:0{p['w']}b}")
        for _ in range(p['k']):
            bits.insert(0, bits.pop())
        return int(''.join(bits), 2)
    if n == 202:
        positions = list(range(p['w']))
        rotated = positions[:]
        for _ in range(p['a'] + p['b']):
            rotated.insert(0, rotated.pop())
        return next(k for k in range(p['w']) if rotated == (positions[-k:] + positions[:-k] if k else positions))
    if n == 203:
        stages = 0
        shift = 1
        while shift < p['w']:
            stages += 1
            shift *= 2
        return len([(stage, bit) for stage in range(stages) for bit in range(p['w'])])
    if n == 204:
        rotated = oracle(201, dict(w=p['w'], x=p['x'], k=1))
        return f"{rotated:b}".count('1')
    if n == 205:
        for index in range(p['w']):
            result = oracle(201, dict(w=p['w'], x=1 << index, k=p['k']))
            if result & (1 << p['j']):
                return index
    if n == 206:
        first = [p['d'][p['s0']], p['d'][2 + p['s0']]]
        return first[p['s1']]
    if n == 207:
        data = [0, 1, 1, 0]
        # Integrate the ideal MUX output over one-ns intervals. This creates
        # pulses despite zero internal path delay: a functional select hazard.
        return sum(data[2 * int(t >= p['s1_time']) + int(t >= p['s0_time'])]
                   for t in range(max(p['s0_time'], p['s1_time']) + 1))
    if n == 208:
        # Apply the stated device voltage inequalities independently, including
        # overlap, rail inputs, asymmetric thresholds and a non-overlap gap.
        off_p = p['gate'] >= p['vdd'] - p['vtp']
        off_n = p['gate'] <= p['vtn']
        return [int(not off_p), int(not off_n)]
    if n == 209:
        rails = {(1, 0, 1): 1, (1, 0, 0): 0, (1, 1, 1): 0.7,
                 (0, 0, 0): 0.3, (0, 1, 1): 'Z'}
        return rails[p['ng'], p['pg'], p['data']]
    if n == 211:
        state, phase, cycles = 0, 0, 0
        while True:
            state = (state + p['en'][phase]) % 6
            phase = (phase + 1) % len(p['en'])
            cycles += 1
            if state == phase == 0:
                return cycles
    if n == 213:
        state = p['start']
        wraps = 0
        for en in p['en']:
            if en:
                if state == 5:
                    state = 0
                    wraps += 1
                else:
                    state += 1
        return wraps
    if n == 210:
        charge_pc = p['c'] * p['v']
        return charge_pc * p['v']
    if n == 212:
        table = {q: (q + 1 if q < 5 else 0) for q in range(8)}
        if p['q'] in (6, 7):
            return table[p['q']]
        return table[p['q']] if p['en'] else p['q']
    if n == 214:
        last, rising = 0, 0
        for level in p['clk']:
            if last == 0 and level == 1:
                rising += 1
            last = level
        return rising
    if n == 215:
        # Divide-by-four output is high during two of four input intervals.
        return sum(p['period'] for state in range(4) if state & 2)
    if n == 216:
        arrivals = [0]
        for _ in range(p['ripple']):
            arrivals.append(arrivals[-1] + p['tcq'])
        return arrivals[-1]
    if n == 217:
        return next(edge for edge in range(p['detect'] + 2) if edge > p['detect'])
    if n == 218:
        # Complete literal DFA with detection output, independent of the
        # author's suffix comparison. Enumerate breadth-first continuations.
        transition = {0: {'0': (0,0), '1': (1,0)}, 1: {'0': (0,0), '1': (2,0)},
                      2: {'0': (3,0), '1': (2,0)}, 3: {'0': (0,0), '1': (1,1)}}
        def final_output(bits):
            state, output = 0, 0
            for bit in bits:
                state, output = transition[state][bit]
            return output
        queue = ['0', '1']
        while queue:
            candidate = queue.pop(0)
            if final_output(p['a'] + candidate) != final_output(p['b'] + candidate):
                return candidate
            queue.extend([candidate + '0', candidate + '1'])
    if n == 219:
        pattern = p['pattern']
        for shift in range(1, len(pattern) + 1):
            occupied = {}
            consistent = True
            for offset in (0, shift):
                for index, bit in enumerate(pattern, offset):
                    if index in occupied and occupied[index] != bit:
                        consistent = False
                    occupied[index] = bit
            if consistent:
                return shift
    if n == 220:
        accepted = [(cycle, bit) for cycle, (valid, bit) in enumerate(p['samples'], 1) if valid]
        bitstring = ''.join(str(bit) for _, bit in accepted)
        return [accepted[m.start() + 3][0] for m in re.finditer(r'(?=0101)', bitstring)]
    if n == 221:
        return len([index for index, v in enumerate(p['valid']) if v])
    if n == 222:
        accepted = [word for valid, word in p['samples'] if valid]
        count = 0
        for word in reversed(accepted):
            if word != p['ref']:
                break
            count += 1
        return count
    if n == 223:
        hits = []
        for i, (v, word) in enumerate(p['samples']):
            for ref in p['refs']:
                if v and ref == word:
                    hits.append(i)
        return len(set(hits))
    if n == 224:
        return sorted(tag for tag in p['accepted'][:p['cut']] if tag not in p['done'])
    if n == 225:
        return next(t for t in range(max(p['times'].values()) + 1)
                    if all(p['times'][tag] <= t for tag in p['snapshot']))
    if n == 226:
        return len([tag for tag in p['done'] if tag in p['snapshot']])
    if n == 227:
        return sum(sum(arrival <= t for arrival in p['arrivals']) for t in range(p['end']))
    if n == 228:
        ages = []
        for start, end in p['pairs']:
            ages.append(len(range(start, end)))
        assert sum(ages) % len(ages) == 0
        return sum(ages) // len(ages)
    if n == 229:
        # Compute a packet-weighted rational mean, rather than averaging means.
        from fractions import Fraction
        mean = sum(Fraction(total, count) * count for total, count in zip(p['sums'], p['counts'], strict=True)) / sum(p['counts'])
        assert mean.denominator == 1
        return mean.numerator
    if n == 230:
        edge_latch = dict(zip(range(4), p['memory'], strict=True))
        captured = edge_latch[p['sampled_addr']]
        assert p['later_addr'] != p['sampled_addr']
        return captured
    if n == 231:
        data, valid = p['old'], 0
        if p['en']:
            data, valid = p['read'], 1
        return [data, valid]
    if n == 232:
        trace = [p['old'], p['new']]
        return trace[{'read-first': 0, 'write-first': 1}[p['policy']]]
    if n == 233:
        ff = [(word, bit) for word in range(4 + p['registered']) for bit in range(p['w'])]
        return len(ff)
    if n == 234:
        mask = [int(p['en'] and address == p['addr']) for address in range(4)]
        return int(''.join(map(str, reversed(mask))), 2)
    if n == 235:
        return next(edge for edge in range(0, p['release'] + p['recovery'] + 2 * p['period'], p['period'])
                    if edge - p['release'] >= p['recovery'])
    if n == 236:
        full_sum = p['a'] + p['b']
        bits = f'{full_sum:05b}'
        return [int(bits[1:3], 2), int(bits[0])]
    if n == 237:
        carry = [(p['a'] + p['b'] + cin) >= 2 ** p['w'] for cin in (0, 1)]
        return [int(carry == [False, True]), int(carry[0])]
    if n == 238:
        possible = [a + b for a in range(2 ** p['a']) for b in range(2 ** p['b'])]
        return next(bits for bits in range(1, 20) if max(possible) < 2 ** bits)
    if n in {239, 240}:
        from fractions import Fraction
        mean = Fraction(p['a'] + p['b'], 2)
        return math.ceil(mean) if n == 239 else round(mean)
    if n == 241:
        product = ''.join(str(p['digit'] + p['digit'] + p['digit']))
        return int(product[-1])
    if n == 242:
        value = p['digit'] + p['digit'] + p['digit']
        return 0 if value < 10 else int(str(value)[0])
    if n == 243:
        legal = list(range(10))
        invalid = [x for x in range(16) if x not in legal]
        return dict(excluded=len(invalid), lowest_invalid=invalid[0], highest_valid=legal[-1],
                    defined_rows=len(legal), output_max=max(d + d + d for d in legal))[p['query']]
    if n == 244:
        count, value = 0, p['x']
        while value > 1:
            value //= 2
            count += 1
        return count
    if n == 245:
        values = set(range(p['w']))
        return next(bits for bits in range(20) if 2 ** bits >= len(values))
    if n == 246:
        quantity = p['r'] + p['r'] + p['bit']
        return int(quantity >= 5)
    if n == 247:
        quotient, remainder = 0, 0
        for bit in f"{p['bits_value']:0{p['width']}b}":
            remainder = remainder + remainder + int(bit)
            digit = 0
            if remainder >= 5:
                remainder -= 5
                digit = 1
            quotient = quotient + quotient + digit
        return quotient
    if n == 248:
        return next(bits for bits in range(20) if 2 ** bits >= p['divisor'])
    if n == 249:
        accepted = []
        for t in p['triggers']:
            if not any(start <= t < start + p['width'] for start in accepted):
                accepted.append(t)
        return len(accepted)
    if n == 250:
        assert all(b - a < p['width'] for a, b in zip(p['triggers'], p['triggers'][1:], strict=False))
        deadline = None
        for t in p['triggers']:
            deadline = t + p['width']
        return deadline
    raise AssertionError(n)


@pytest.mark.parametrize('check', CHECKS, ids=lambda row: row['key'])
def test_case_matches_independent_oracle_and_selected_choice(check):
    expected = oracle(check['task'], check['inputs'])
    assert expected == check['expected']
    assert sum(x == expected for x in check['options']) == 1
    row = BY_KEY[check['key']]
    assert check['options'][row['correct']] == expected
    rendered = json.dumps(expected, ensure_ascii=False, separators=(',', ':')) if isinstance(expected, list) else str(expected)
    assert row['choices'][row['correct']] == {'he': rendered, 'en': rendered}


def test_bilingual_card_schema_sources_brevity_and_no_prior_identity_reuse():
    prep = {row['id'] for row in read(ROOT / 'interview_preparation/questions.json')['questions']}
    prior = [row for file in CONTENT.glob('fundamentals-*.json')
             if file.name not in {'fundamentals-hardware-500.json', 'fundamentals-reasoning-500.json',
                                  'fundamentals-code-500.json', 'fundamentals-revisions.json'}
             for row in read(file)]
    assert len(CARDS) == 50
    assert {c['id'] for c in CARDS} == {f'quick-hw-{n}' for n in range(201, 251)}
    assert not ({c['id'] for c in CARDS} & {c['id'] for c in prior})
    for card in CARDS:
        assert set(card['interviewIds']) <= prep and card['interviewIds']
        assert card['topic'] in {'gates', 'bits', 'sequential', 'states', 'electronics'}
        assert not {'company', 'solution_review', 'release_approval'} & set(card)
        for field, limit in [('title', 12), ('prompt', 50), ('answer', 65), ('takeaway', 20)]:
            assert set(card[field]) == {'he', 'en'}
            for lang, value in card[field].items():
                assert value == value.strip() and value and len(value.split()) <= limit, (card['id'], field, lang)
                assert '\ufffd' not in value
                if lang == 'en':
                    assert not re.search(r'[\u0590-\u05ff]', value)
    for lang, field in itertools.product(('he', 'en'), ('title', 'prompt')):
        texts = [c[field][lang].casefold().strip() for c in [*prior, *CARDS]]
        assert len(texts) == len(set(texts))


def test_five_distinct_drafts_four_choices_and_balanced_answer_positions():
    assert len(QUIZ) == len(CHECKS) == len(BY_KEY) == 250
    for card in CARDS:
        rows = [q for q in QUIZ if q['source_key'] == card['id']]
        assert sorted(q['variant'] for q in rows) == [1, 2, 3, 4, 5]
        for lang in ('he', 'en'):
            assert len({q['prompt'][lang] for q in rows}) == 5
        for q in rows:
            assert q['key'] == f"{q['source_key']}-v{q['variant']}"
            assert q['status'] == 'draft' and q['topic'] == card['topic']
            assert len(q['choices']) == 4 and type(q['correct']) is int and 0 <= q['correct'] < 4
            for lang in ('he', 'en'):
                assert len({c[lang] for c in q['choices']}) == 4
                for text in [q['prompt'][lang], q['explanation'][lang], *(c[lang] for c in q['choices'])]:
                    assert text and text == text.strip() and '\ufffd' not in text
                    if lang == 'en':
                        assert not re.search(r'[\u0590-\u05ff]', text)
    counts = Counter(q['correct'] for q in QUIZ)
    assert max(counts.values()) - min(counts.values()) <= 1


def test_generator_reproduces_all_owned_artifacts():
    spec = importlib.util.spec_from_file_location('hardware500', ROOT / 'backend/scripts/quiz_authoring/hardware_500.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    questions, checks = module.build()
    assert questions == QUIZ and checks == CHECKS and module.CARDS == CARDS


def test_counterexample_and_boundary_coverage():
    assert oracle(219, dict(pattern='101101')) == 3
    assert oracle(220, dict(samples=[[1,0],[1,1],[0,0],[1,0],[1,1]])) == [5]
    assert oracle(218, dict(a='1', b='11')) == '01'
    assert oracle(212, dict(q=7, en=0)) == 0
    assert oracle(222, dict(ref=5, samples=[[1, 5], [0, 2], [1, 5]])) == 2
    assert oracle(224, dict(accepted=[1, 2, 3], cut=2, done=[1, 3])) == [2]
    assert oracle(246, dict(r=4, bit=1)) == 1
    assert oracle(249, dict(width=5, triggers=[0, 2, 5])) == 2
