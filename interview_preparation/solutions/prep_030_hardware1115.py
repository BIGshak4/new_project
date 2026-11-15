"""Five MAX/MIN cells with either straight or crossing single faults."""
from itertools import combinations, permutations

NETWORK = ((0, 1), (2, 3), (0, 2), (1, 3), (1, 2))
HYPOTHESES = (None,) + tuple((index, mode) for index in range(5)
                           for mode in ("straight", "cross"))
TESTS = ((1, 2, 3, 4), (1, 3, 2, 4), (4, 3, 2, 1))


def run(values, hypothesis=None):
    wires = list(values)
    if len(wires) != 4 or hypothesis not in HYPOTHESES:
        raise ValueError("four wires and one declared hypothesis required")
    for index, (upper, lower) in enumerate(NETWORK):
        a, b = wires[upper], wires[lower]
        if hypothesis == (index, "straight"):
            pair = a, b
        elif hypothesis == (index, "cross"):
            pair = b, a
        else:
            pair = (a, b) if a >= b else (b, a)
        wires[upper], wires[lower] = pair
    return tuple(wires)


def signatures():
    return {hypothesis: tuple(run(test, hypothesis) for test in TESTS)
            for hypothesis in HYPOTHESES}


def diagnose(observed):
    observed = tuple(map(tuple, observed))
    matches = [hypothesis for hypothesis, signature in signatures().items()
               if observed == signature]
    if len(matches) != 1:
        raise ValueError("observation violates this single-fault model")
    return matches[0]


def minimum_fixed_test_count():
    probes = tuple(permutations((1, 2, 3, 4)))
    outputs = [tuple(run(probe, hypothesis) for hypothesis in HYPOTHESES)
               for probe in probes]
    assert all(len(set(row)) < 11 for row in outputs)
    assert all(len(set(zip(outputs[i], outputs[j]))) < 11
               for i, j in combinations(range(24), 2))
    assert len(set(signatures().values())) == 11
    return 3
