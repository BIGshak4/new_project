"""Exhaustive low-bit selection versus independent numerical bit scanning."""
import json
import random
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_107_lowest_onehot_gates import lowest_onehot

checked = 0
for width in range(1, 13):
    for value in range(1 << width):
        expected = next((2**index for index in range(width) if value // (2**index) % 2), 0)
        result = lowest_onehot(value, width)
        assert result == expected and result & value == result
        assert result == 0 or result.bit_count() == 1
        checked += 1
rng = random.Random(107)
sampled = 0
for width in (13, 31, 32, 64, 127, 257):
    for _ in range(100):
        value = rng.randrange(1 << width)
        result = lowest_onehot(value, width)
        expected = next((1 << index for index in range(width) if (value >> index) % 2), 0)
        assert result == expected
        sampled += 1
assert f"{lowest_onehot(0b1110100, 7):07b}" == "0000100"
for value, width in ((0, 0), (0, -1), (-1, 8), (256, 8), (True, 8), (1, True)):
    try:
        lowest_onehot(value, width)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid vector accepted")
record = {
    "question_id": "PREP-107", "checked_on": "2026-10-24", "status": "passed",
    "exhaustive_vectors_width_1_through_12": checked, "seeded_wide_vectors": sampled,
    "invalid_vectors_rejected": 6, "source_example": "1110100 -> 0000100",
    "oracle": "Independent least-index numerical scan; subset/one-hot invariants.",
    "scope": "Basic Boolean gate-prefix model, including zero; no subtractor in the proposed datapath, HDL compilation or physical delay/minimum-area claim.",
}
(BANK / "checks/prep-107-verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
