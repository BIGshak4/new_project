"""Finite functional checks against last-enabled and sampled-edge oracles."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_083_mux_latch_register import (
    MasterSlave,
    latch,
    register_enabled,
)


def main():
    rows = streams = steps = edge_traces = edge_steps = 0
    for q, data, en in itertools.product(range(2), repeat=3):
        assert latch(q, data, en) == (en * data + (1 - en) * q)
        rows += 1
    for size in range(7):
        for events in itertools.product(tuple(itertools.product(range(2), repeat=2)), repeat=size):
            for initial in (0, 1):
                q = initial
                enabled_data = [initial]
                for data, en in events:
                    q = latch(q, data, en)
                    if en:
                        enabled_data.append(data)
                    assert q == enabled_data[-1]
                    steps += 1
                streams += 1
    # Each cycle has two low-phase data values, then a stable rising edge,
    # then an unrelated high-phase value that must not reach Q.
    for data in itertools.product(range(2), repeat=12):
        for initial in (0, 1):
            circuit = MasterSlave(initial, initial)
            expected = initial
            for offset in range(0, 12, 3):
                a, captured, high_change = data[offset:offset + 3]
                assert circuit.settle(a, 0) == expected
                assert circuit.settle(captured, 0) == expected
                expected = captured
                assert circuit.settle(captured, 1) == expected
                assert circuit.settle(high_change, 1) == expected
                edge_steps += 4
            edge_traces += 1
    word_rows = 0
    for old, data, en in itertools.product(range(16), range(16), range(2)):
        assert register_enabled(old, data, en, 4) == (data if en else old)
        word_rows += 1
    result = {"question_id": "PREP-083", "status": "passed", "latch_truth_rows": rows,
              "latch_streams": streams, "latch_steps": steps, "master_slave_traces": edge_traces,
              "master_slave_settled_phases": edge_steps, "four_bit_enable_rows": word_rows,
              "scope": "Ideal stable-phase Python Boolean model; no HDL compilation, analogue timing, metastability, synthesis, STA or hardware verification",
              "professional_review": "pending"}
    (BANK / "checks/prep-083-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
