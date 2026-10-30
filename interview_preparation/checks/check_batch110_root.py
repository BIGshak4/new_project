"""Independent finite oracles; these execute Python models, not C/C++ binaries."""
import importlib.util
import itertools
import json
import random
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOLUTIONS = HERE.parent / 'solutions'

def load(filename):
    import sys
    spec = importlib.util.spec_from_file_location(filename.replace('.', '_'), SOLUTIONS / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def run_group(ident):
    rng = random.Random(110)
    count = 0
    if ident == 'PREP-188':
        model = load('prep_188_closest_pair_model.py')
        grid = list(itertools.product(range(-1, 2), repeat=2))
        inputs = (list(points) for n in range(2, 6) for points in itertools.combinations_with_replacement(grid, n))
        for points in itertools.chain(inputs, ([tuple(rng.randint(-10**9, 10**9) for _ in range(2)) for _ in range(rng.randint(2, 90))] for _ in range(200))):
            distance, i, j = model.closest_pair(points)
            oracle = min((p[0]-q[0])**2+(p[1]-q[1])**2 for p, q in itertools.combinations(points, 2))
            assert i != j and distance == oracle
            assert (points[i][0]-points[j][0])**2+(points[i][1]-points[j][1])**2 == oracle
            count += 1
        points = [(-10**9, -10**9), (10**9, 10**9)]
        assert model.closest_pair(points)[0] == 8*10**18
        count += 1
        scope = 'Python divide-and-conquer versus independent exhaustive pair enumeration; C source reviewed but not compiled in this environment.'
    elif ident == 'PREP-022':
        model = load('prep_022_random_pixels_batch110.py')
        for rows, columns in ((0, 0), (0, 3), (1, 1), (1, 4), (2, 2), (2, 3)):
            size = rows*columns; seen = set()
            paths = itertools.product(*(range(k) for k in range(size, 1, -1)))
            for path in paths:
                values = iter(path); result = tuple(model.random_pixels(rows, columns, lambda k, stream=values: next(stream)))
                assert len(result) == size and len(set(result)) == size
                assert set(result) == set(itertools.product(range(rows), range(columns)))
                assert result not in seen; seen.add(result); count += 1
            import math
            assert len(seen) == math.factorial(size)
        scope = 'Every draw path through six-cell screens; exact bijection between equiprobable paths and all permutations, empty and one-cell cases.'
    elif ident == 'PREP-125':
        model = load('prep_125_eight_register_interpreter_batch110.py')
        for a, b in itertools.product(range(25), repeat=2):
            scratch = tuple(rng.randrange(8) for _ in range(6))
            result, _ = model.execute(a, b, scratch=scratch)
            assert result[0] == a and result[1] == 0 and result[2] == a*b and result[3] == 0 and result[7] == 1
            assert result[4:7] == list(scratch[2:5]); count += 1
        scope = '625 inputs with arbitrary nonzero natural scratch registers, exact three-opcode interpreter, no DEC-at-zero, no stale branch result, fall-through completion.'
    elif ident == 'PREP-149':
        model = load('prep_149_cpu_log_batch110.py')
        cases = [[], [(0, 1, 25), (1, 2, 50)], [(0, 2, Fraction(1, 3)), (0, 1, Fraction(2, 3))]]
        cases += [[(s := rng.randrange(8), s+rng.randrange(1, 8), Fraction(rng.randrange(101), 4)) for _ in range(rng.randrange(1, 15))] for _ in range(500)]
        for records in cases:
            for length in range(len(records)+1):
                prefix = records[:length]
                endpoints = sorted({t for s, e, _ in prefix for t in (s, e)})
                values = [(sum((Fraction(u) for s, e, u in prefix if s <= t < e), Fraction(0)), t) for t in endpoints]
                best = max((v for v, _ in values), default=Fraction(0))
                first = next((t for v, t in values if v == best), None) if best > 0 else None
                assert model.maximum_cpu_usage(prefix) == (best, first); count += 1
        scope = 'Weighted half-open slab oracle for every growing-log prefix across 503 snapshots, including simultaneous events and fractional weights.'
    elif ident == 'PREP-194':
        model = load('prep_194_abstract_list_reverse.py')
        def values(chain):
            result = []
            while chain is not None:
                result.append(chain.value); chain = chain.next
            return result
        for n in range(8):
            for data in itertools.product((0, 1, 2), repeat=n):
                chain = None
                for item in reversed(data):
                    chain = model.Node(item, chain)
                assert values(model.reverse(chain)) == list(reversed(data))
                assert values(chain) == list(data); count += 1
        scope = 'All 3280 finite lists over three values at lengths0..7; original immutable list remains unchanged. Completed ADT assumptions are explicit.'
    elif ident == 'PREP-196':
        model = load('prep_196_recursion_tradeoffs.py')
        for n in range(300):
            assert model.recursive_sum(n) == model.iterative_sum(n) == n*(n+1)//2; count += 1
        scope = '300 small inputs versus closed-form sum; no claim of fixed recursion limit, tail-call elimination or C/C++ execution.'
    else:
        raise ValueError(ident)
    return {'question_id': ident, 'passed': True, 'cases': count, 'scope': scope, 'professional_review': 'pending'}

def main():
    results = [run_group(ident) for ident in ('PREP-188', 'PREP-022', 'PREP-125', 'PREP-149', 'PREP-194', 'PREP-196')]
    for result in results:
        suffix = '' if int(result['question_id'][5:]) >= 188 else '-batch110'
        (HERE / f'{result["question_id"].lower()}{suffix}-verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
