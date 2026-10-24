"""SR latch fixed points, legal traces and an independent sampled SR oracle."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_106_sr_storage_gates import gated_sr_latch, master_slave_phase, sr_latch


def expected(q, s, r):
    return 1 if s else (0 if r else q)


valid_rows = 0
for q, s, r in itertools.product((0, 1), repeat=3):
    if s and r:
        try:
            sr_latch(q, s, r)
        except ValueError:
            pass
        else:
            raise AssertionError("forbidden request was predicted")
    else:
        result = sr_latch(q, s, r)
        assert result == expected(q, s, r)
        # Independently solve both physical NOR Boolean fixed-point equations.
        fixed = {(out, other) for out, other in itertools.product((0, 1), repeat=2)
                 if out == int(not (r or other)) and other == int(not (s or out))}
        assert (result, 1 - result) in fixed
        assert len(fixed) == (2 if s == r == 0 else 1)
        valid_rows += 1
for q, s, r in itertools.product((0, 1), repeat=3):
    assert gated_sr_latch(q, s, r, 0) == q
legal = ((0, 0), (1, 0), (0, 1))
streams = updates = 0
for initial in (0, 1):
    for length in range(8):
        for requests in itertools.product(legal, repeat=length):
            q = reference = initial
            for s, r in requests:
                q = sr_latch(q, s, r)
                reference = expected(reference, s, r)
                assert q == reference
                updates += 1
            streams += 1
# Master/slave composed from D-latch behavior must obey SR at the rising edge,
# even when its stale master differed initially, and ignore high-phase changes.
phase_checks = 0
for initial, stale_master, low_request, high_request in itertools.product((0, 1), (0, 1), legal, legal):
    master, q = master_slave_phase(stale_master, initial, *low_request, 0)
    assert q == initial
    master, q = master_slave_phase(master, q, *low_request, 1)
    assert q == expected(initial, *low_request)
    master, q_after = master_slave_phase(master, q, *high_request, 1)
    assert q_after == q
    phase_checks += 1
record = {
    "question_id": "PREP-106", "checked_on": "2026-10-24", "status": "passed",
    "legal_q_s_r_rows": valid_rows, "disabled_hold_rows": 8,
    "legal_streams": streams, "latch_updates": updates, "master_slave_phase_cases": phase_checks,
    "oracle": "Independent set/reset/hold branching plus exhaustive complementary NOR fixed points; opposite-phase D-latch composition checked against edge SR behavior.",
    "scope": "Ideal stable binary states and non-overlapping phases. Forbidden requests are rejected; no prediction of release races, analog startup, metastability, HDL simulation or physical timing.",
}
(BANK / "checks/prep-106-verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
