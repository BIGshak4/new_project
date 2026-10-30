"""Full nodal Kirchhoff solver, independent of the four-distance formula."""

import importlib.util
import itertools
import json
import random
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "resistor154", BANK / "solutions/prep_154_hidden_central_resistance.py"
)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def ohmmeter(resistances, a, b):
    """Inject one ampere at terminal a; ground b; all other leaves floating."""
    edges = [(0, 6), (1, 6), (2, 6), (6, 7), (7, 3), (7, 4), (7, 5)]
    nodes = [n for n in range(8) if n != b]
    index = {n: i for i, n in enumerate(nodes)}
    matrix = [[Fraction(0) for _ in range(8)] for _ in range(7)]
    for (u, v), resistance in zip(edges, resistances, strict=True):
        conductance = 1 / Fraction(resistance)
        for x, y in ((u, v), (v, u)):
            if x == b:
                continue
            matrix[index[x]][index[x]] += conductance
            if y != b:
                matrix[index[x]][index[y]] -= conductance
    matrix[index[a]][7] = 1
    for column in range(7):
        pivot = next(row for row in range(column, 7) if matrix[row][column])
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
        scale = matrix[column][column]
        matrix[column] = [value / scale for value in matrix[column]]
        for row in range(7):
            if row == column:
                continue
            factor = matrix[row][column]
            matrix[row] = [x - factor * y for x, y in zip(matrix[row], matrix[column], strict=True)]
    return matrix[index[a]][7]


def run_checks():
    rng = random.Random(154)
    networks = list(itertools.product((1, 2), repeat=7))
    networks.extend(tuple(rng.randint(1, 10000) for _ in range(7)) for _ in range(200))
    measurements = 0
    for hidden in networks:
        calls = []

        def measure(a, b, calls=calls, hidden=hidden):
            calls.append((a, b))
            return ohmmeter(hidden, a, b)

        assert model.infer_central_resistance(measure) == hidden[3]
        assert calls == [(0, 3), (1, 4), (0, 1), (3, 4)]
        measurements += len(calls)
    base = (4, 5, 6, 7, 8, 9, 10)
    shifted = (3, 4, 5, 8, 8, 9, 10)
    for a, b in itertools.product(range(3), range(3, 6)):
        assert ohmmeter(base, a, b) == ohmmeter(shifted, a, b)
    assert base[3] != shifted[3]
    return {
        "question_id": "PREP-154",
        "status": "passed",
        "exhaustive_positive_binary_resistor_networks": 128,
        "seeded_wide_networks": 200,
        "independent_exact_nodal_solves": measurements,
        "cross_only_nonidentifiability_readings": 9,
        "scope": "Exact Fraction Gaussian elimination of the full eight-node conductance network with one-ampere terminal injection, other leaves floating. 328 hidden networks, four readings each; separate cross-only counterexample. No physical ohmmeter, SPICE or minimum across arbitrary shorting/multiport methods.",
    }


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-154-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))
