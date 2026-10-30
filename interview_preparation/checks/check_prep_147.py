"""Complementary-enable capture traces compared with pair permutation."""

import importlib.util
import json
import random
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "swap147", BANK / "solutions/prep_147_complementary_load_alu_swap.py"
)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def one_case(x, y, width):
    trace = model.swap_trace(x, y, width)
    assert trace == [(x, y), (x ^ y, y), (x ^ y, x), (y, x)]
    for load, before, after in zip((0, 1, 0), trace[:-1], trace[1:], strict=True):
        assert before[1 - load] == after[1 - load]
        assert all(0 <= value < 1 << width for value in after)


def run_checks():
    exhaustive = 0
    for width in range(1, 9):
        for x in range(1 << width):
            for y in range(1 << width):
                one_case(x, y, width)
                exhaustive += 1
    rng = random.Random(147)
    random_cases = 0
    for width in (16, 32, 64, 127):
        for _ in range(100):
            one_case(rng.getrandbits(width), rng.getrandbits(width), width)
            random_cases += 1
    return {
        "question_id": "PREP-147",
        "status": "passed",
        "exhaustive_pairs_widths_one_through_eight": exhaustive,
        "seeded_wide_pairs": random_cases,
        "controlled_capture_edges": 3 * (exhaustive + random_cases),
        "scope": "Ideal fixed-width XOR/edge-enable Python model, complete small-state traces and seeded wide values. Assumes edge-triggered capture and no extra capture edges; no latch-race, HDL or physical timing claim.",
    }


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-147-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))
