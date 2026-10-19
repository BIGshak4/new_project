"""Check pulse phase, duration and resets using elapsed-edge arithmetic."""
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("third_clock", ROOT / "solutions/prep_048_every_third_clock.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def verify():
    reset_traces = 0
    sampled_edges = 0
    for length in range(16):
        for resets in itertools.product((False, True), repeat=length):
            circuit = MODEL.EveryThirdClock()
            elapsed = 0
            for reset in resets:
                elapsed = 0 if reset else elapsed + 1
                expected = int(elapsed > 0 and elapsed % 3 == 0)
                assert circuit.step(reset) == expected
                assert circuit.count == elapsed % 3
                sampled_edges += 1
            reset_traces += 1
    circuit = MODEL.EveryThirdClock()
    outputs = [circuit.step() for _ in range(3000)]
    assert outputs == [0, 0, 1] * 1000
    assert sum(outputs) == 1000
    assert not any(a and b for a, b in itertools.pairwise(outputs))
    assert circuit.step(True) == 0
    assert [circuit.step() for _ in range(6)] == [0, 0, 1, 0, 0, 1]
    return {
        "question": "PREP-048", "status": "passed",
        "all_reset_traces_lengths_0_to_15": reset_traces,
        "sampled_edges_in_reset_trace_exhaustion": sampled_edges,
        "continuous_cycles": 3000, "continuous_pulses": 1000,
        "scope": "Python clock-edge model matched an independent elapsed-edge modulo oracle. SystemVerilog supplied but not HDL-simulated, synthesized or physically timed."
    }


if __name__ == "__main__":
    report = verify()
    (ROOT / "checks/prep-048-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
