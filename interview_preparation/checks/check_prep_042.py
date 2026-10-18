"""Exhaust sample streams against an independent difference-based oracle."""
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rising_edge", ROOT / "solutions/prep_042_rising_edge.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def verify():
    streams = 0
    for initial in (0, 1):
        for length in range(13):
            for samples in itertools.product((0, 1), repeat=length):
                detector = MODEL.RisingEdgeDetector(initial)
                previous = initial
                for sample in samples:
                    expected = int(sample - previous == 1)
                    assert detector.step(sample) == expected
                    previous = sample
                streams += 1
    reset_cases = 0
    for samples in itertools.product((0, 1), repeat=8):
        for reset_at in range(8):
            detector = MODEL.RisingEdgeDetector()
            previous = 0
            for i, sample in enumerate(samples):
                reset = i == reset_at
                expected = 0 if reset else int(sample - previous == 1)
                assert detector.step(sample, reset) == expected
                previous = 0 if reset else sample
            reset_cases += 1
    detector = MODEL.RisingEdgeDetector()
    assert [detector.step(x) for x in (0, 1, 1, 0, 1)] == [0, 1, 0, 0, 1]
    detector = MODEL.RisingEdgeDetector()
    assert [detector.step(1) for _ in range(100)] == [1] + [0] * 99
    return {"question": "PREP-042", "status": "passed", "binary_streams_lengths_0_to_12_two_initial_states": streams,
            "midstream_reset_traces": reset_cases, "held_high_cycles": 100,
            "scope": "Python clock-edge model and independent oracle; SystemVerilog source supplied but not HDL-simulated or physically timed."}


if __name__ == "__main__":
    result = verify()
    (ROOT / "checks/prep-042-verification.json").write_bytes(
        (json.dumps(result, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8"))
    print(json.dumps(result))
