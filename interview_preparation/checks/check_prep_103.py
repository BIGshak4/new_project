"""Independent DFF oracle for all short input streams from both initial bits."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_103_dff_from_tff import dff_from_tff, tff, trace

for q, data in itertools.product((0, 1), repeat=2):
    assert dff_from_tff(q, data) == data
    assert dff_from_tff(q, data, rising_edge=False) == q
for q, toggle in itertools.product((0, 1), repeat=2):
    assert tff(q, toggle) == (1 - q if toggle else q)
streams = edges = 0
for initial in (0, 1):
    for length in range(11):
        for samples in itertools.product((0, 1), repeat=length):
            assert trace(samples, initial=initial) == list(samples)
            streams += 1
            edges += length
record = {
    "question_id": "PREP-103", "checked_on": "2026-10-24", "status": "passed",
    "q_data_truth_rows": 4, "hold_without_edge_cases": 4,
    "exhaustive_streams": streams, "sampling_edges": edges,
    "oracle": "A separate ideal DFF directly stores each sampled data bit; TFF oracle uses conditional inversion.",
    "scope": "Both concrete initial states, two-state sampled logic only. No reset assumption, HDL compilation, analog initialization, metastability or physical timing simulation.",
}
(BANK / "checks/prep-103-verification.json").write_text(
    json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
