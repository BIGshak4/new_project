"""Exhaust every bottle and all ten-bit endpoint outcomes, PREP-073."""

import json
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = spec_from_file_location(
    "bottle_solution", BANK / "solutions/prep_073_binary_bottles.py"
)
solution = module_from_spec(spec)
spec.loader.exec_module(solution)


def run():
    groups = solution.tasting_groups()
    assert len(groups) == 10
    patterns = set()
    for bottle in range(1, 1001):
        # Observable outcomes obtained by actual membership in each pooling group.
        observed = tuple(bottle in group for group in groups)
        assert observed not in patterns
        patterns.add(observed)
        assert solution.decode(observed) == bottle
        # Independent division/remainder label oracle (not bit-mask code).
        value = bottle - 1
        expected = []
        for _ in range(10):
            value, remainder = divmod(value, 2)
            expected.append(bool(remainder))
        assert observed == tuple(expected) and value == 0
    assert solution.decode((False,) * 10) == 1
    assert all(1 not in group for group in groups)
    invalid_patterns = 0
    for outcomes in product((False, True), repeat=10):
        if outcomes not in patterns:
            try:
                solution.decode(outcomes)
            except ValueError:
                invalid_patterns += 1
            else:
                raise AssertionError(outcomes)
    assert invalid_patterns == 24
    assert 2**9 < 1000 <= 2**10
    malformed = [(), (False,) * 9, (False,) * 11, (0,) * 10, ("0",) * 10]
    for value in malformed:
        try:
            solution.decode(value)
        except ValueError:
            pass
        else:
            raise AssertionError(value)
    result = {
        "question_id": "PREP-073",
        "checked_on": "2026-10-21",
        "status": "passed_python_model",
        "unique_poisoned_bottles_decoded": 1000,
        "total_endpoint_patterns": 1024,
        "unused_patterns_rejected": invalid_patterns,
        "malformed_inputs_rejected": len(malformed),
        "all_survive_case": "Bottle 1 has internal label zero and is deliberately absent from all pools.",
        "method": "Constructed ten pooling groups; simulated every possible poisoned bottle using membership; checked independent repeated-division code oracle, injectivity and all unused ten-bit patterns.",
        "limits": "Abstract deterministic one-batch puzzle only; no real tasting, chemical validation or human professional approval. Information lower bound is proved separately.",
    }
    (BANK / "checks/prep-073-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
