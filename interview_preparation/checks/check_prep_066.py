"""Exhaustive independent pair enumeration for one stock transaction."""
import importlib.util
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prep066", ROOT / "solutions/prep_066_best_stock_trade.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def oracle(prices, mandatory):
    candidates = [(i, j, prices[j] - prices[i])
                  for i in range(len(prices)) for j in range(i + 1, len(prices))
                  if mandatory or prices[j] > prices[i]]
    return min(candidates, key=lambda t: (-t[2], t[0], t[1])) if candidates else None


def main():
    count = 0
    for length in range(8):
        for prices in itertools.product(range(4), repeat=length):
            for mandatory in (False, True):
                assert model.best_trade(prices, mandatory=mandatory) == oracle(prices, mandatory), (prices, mandatory)
                count += 1
    rng = random.Random(6601)
    random_cases = 500
    for _ in range(random_cases):
        prices = [rng.randrange(10**80) for _ in range(rng.randrange(2, 31))]
        for mandatory in (False, True):
            assert model.best_trade(prices, mandatory=mandatory) == oracle(prices, mandatory)
    examples = [[], [5], [9, 8, 7], [3, 3], [3, 1, 1, 5, 5], [7, 1, 5, 3, 6, 4]]
    report = {"question_id": "PREP-066", "checked_on": "2026-10-21", "status": "passed_python_code",
              "exhaustive_input_arrays": count // 2, "contracts_per_array": 2, "exhaustive_checks": count,
              "exhaustive_domain": "All lengths 0..7 over prices 0..3", "random_arrays": random_cases,
              "random_contract_checks": 2 * random_cases,
              "examples": [{"prices": p, "optional": model.best_trade(p), "mandatory": model.best_trade(p, mandatory=True)} for p in examples],
              "oracle": "Enumerate all legal buy<sell pairs, discard nonpositive trades only in optional mode; sort by descending profit, then ascending buy and sell.",
              "scope": "Executed Python implementation; exhaustive finite domain plus deterministic large-integer samples. Complexity proven separately; no independent human expert approval."}
    (ROOT / "checks/prep-066-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
