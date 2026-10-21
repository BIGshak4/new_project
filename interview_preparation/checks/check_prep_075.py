"""Independent specification comparisons for PREP-075 word-per-macro banking."""
import itertools
import json
import random
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_075_banked_single_port import BankedOneReadOneWrite


def main():
    exhaustive = random_steps = 0
    # Check every one-step request from every initialized memory of depths 1..4.
    for n in range(1, 5):
        for values in itertools.product(range(2), repeat=n):
            for rd, wr, ra, wa, data in itertools.product(range(2), range(2), range(n), range(n), range(2)):
                dut = BankedOneReadOneWrite(n, 1)
                for i, value in enumerate(values):
                    dut.edge(False, 0, True, i, value)
                valid, got = dut.edge(bool(rd), ra, bool(wr), wa, data)
                expected = data if wr and ra == wa else values[ra]
                assert valid == bool(rd)
                if rd:
                    assert got == expected
                assert [b.mem[0] for b in dut.banks] == [data if wr and i == wa else value for i, value in enumerate(values)]
                assert all(all(v is None for v in bank.mem[1:]) for bank in dut.banks)
                exhaustive += 1
    rng = random.Random(75021)
    for n in (1, 2, 3, 8, 17):
        dut = BankedOneReadOneWrite(n, 8)
        oracle = [None] * n
        last_output = None
        for _ in range(10000):
            rd, wr = bool(rng.randrange(2)), bool(rng.randrange(2))
            ra, wa, data = rng.randrange(n), rng.randrange(n), rng.randrange(256)
            reset = rng.randrange(67) == 0
            valid, got = dut.edge(rd, ra, wr, wa, data, reset)
            if not reset:
                if wr:
                    oracle[wa] = data  # write-first contract
                if rd:
                    last_output = oracle[ra]
            assert valid == bool(rd and not reset)
            # Data is meaningful only when valid; an inactive mux-selected bank
            # output can later change during writes? Primitive output holds, so
            # this model also preserves last data when no read is requested.
            assert got == last_output
            assert [b.mem[0] for b in dut.banks] == oracle
            random_steps += 1
    evidence = {"question_id": "PREP-075", "status": "passed", "exhaustive_one_step_cases": exhaustive,
                "random_trace_edges": random_steps, "random_seed": 75021,
                "depths_in_trace": [1, 2, 3, 8, 17],
                "coverage": "All rd/wr/ra/wa/data cases for every 1-bit initialized memory depth1..4; 50,000 mixed/reset/collision edges vs separate array specification; unwritten values retained as None",
                "scope": "Python synchronous functional model, primitive read/write mutual exclusion asserted; no HDL simulation, synthesis or physical timing verification",
                "professional_review": "pending"}
    (BANK / "checks/prep-075-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
