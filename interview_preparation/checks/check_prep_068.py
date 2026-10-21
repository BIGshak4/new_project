"""Independent ordered oracle plus explicit overflow-boundary coverage."""
import ast
import importlib.util
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "solutions/prep_068_max_without_comparisons.py"
spec = importlib.util.spec_from_file_location("prep068", PATH)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def main():
    tree = ast.parse(PATH.read_text(encoding="utf-8"))
    forbidden = (ast.Compare, ast.IfExp, ast.If, ast.While, ast.For)
    assert not any(isinstance(node, forbidden) for node in ast.walk(tree))
    calls = [node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    assert calls == ["abs"], calls
    exhaustive = 0
    for a, b in itertools.product(range(-128, 128), repeat=2):
        expected = max(a, b)
        assert model.max_without_comparisons(a, b) == expected
        assert model.max_i32_model(a, b) == expected
        exhaustive += 1
    boundaries = [-(1 << 31), -(1 << 31) + 1, -65536, -1, 0, 1, 65536, (1 << 31) - 2, (1 << 31) - 1]
    for a, b in itertools.product(boundaries, repeat=2):
        assert model.max_without_comparisons(a, b) == model.max_i32_model(a, b) == max(a, b)
    rng = random.Random(6801)
    random_count = 10000
    for _ in range(random_count):
        a, b = (rng.randrange(-(1 << 31), 1 << 31) for _ in range(2))
        assert model.max_i32_model(a, b) == max(a, b)
    big_count = 500
    for _ in range(big_count):
        a, b = (rng.randrange(-(1 << 2048), 1 << 2048) for _ in range(2))
        assert model.max_without_comparisons(a, b) == max(a, b)
    # Counterexample to blindly taking the wrapped subtraction's sign.
    a, b = (1 << 31) - 1, -(1 << 31)
    wrapped_sign = ((a - b) & ((1 << 32) - 1)) >> 31
    assert wrapped_sign == 1 and a > b
    report = {"question_id": "PREP-068", "checked_on": "2026-10-21", "status": "passed_python_implementation_and_fixedwidth_model",
              "exhaustive_signed8_pairs_in_both_methods": exhaustive, "signed32_boundary_pairs": len(boundaries)**2,
              "signed32_seeded_random_pairs": random_count, "exact_2048_bit_pairs": big_count,
              "source_constraint_check": "Python AST contains no comparisons, conditionals or loops; the only function call is abs in the declared abs-permitted method.",
              "overflow_counterexample": {"a": a, "b": b, "wrapped_difference_sign": wrapped_sign, "correct_max": a},
              "oracle": "Independent Python builtin max in checks only.",
              "scope": "Python code and uint32 arithmetic model executed. Supplied C++ source was NOT compiled or run; no machine-code branch, timing or constant-time-security claim. Independent human expert review pending."}
    (ROOT / "checks/prep-068-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
