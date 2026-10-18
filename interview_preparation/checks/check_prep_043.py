"""Compare every short stream with a suffix oracle and test a persistent OPEN variant."""
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("serial_lock", ROOT / "solutions/prep_043_serial_lock.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def verify():
    cases = 0
    for length in range(9):
        for chars in itertools.product("ABCDX", repeat=length):
            detector = MODEL.SequenceDetector()
            lock = MODEL.PersistentLock()
            text = ""
            ever_detected = False
            for char in chars:
                text += char
                expected = int(text.endswith("ABCD"))
                assert detector.step(char) == expected, text
                ever_detected = ever_detected or bool(expected)
                assert lock.step(char) == int(ever_detected), text
                longest = max(k for k in range(4) if text.endswith("ABCD"[:k]))
                assert detector.state == longest
            cases += 1
    examples = {"ABCD": [4], "ABCDABCD": [4, 8], "AABCD": [5], "ABABCD": [6],
                "ABCABCD": [7], "ABXCD": [], "ABDC": [], "ABC": []}
    for text, positions in examples.items():
        detector = MODEL.SequenceDetector()
        assert [i + 1 for i, char in enumerate(text) if detector.step(char)] == positions
    detector = MODEL.SequenceDetector()
    for char in "ABC":
        detector.step(char)
    assert detector.step("D", reset=True) == 0 and detector.state == 0
    assert detector.step("D") == 0
    lock = MODEL.PersistentLock()
    for char in "ABCD":
        lock.step(char)
    assert lock.step("X") == 1
    assert lock.step("X", reset=True) == 0
    assert lock.step("D") == 0
    return {"question": "PREP-043", "status": "passed", "streams_over_ABCDX_lengths_0_to_8": cases,
            "explicit_trace_cases": len(examples), "suffix_invariant_checked": True,
            "persistent_and_pulse_models_checked": True, "midstream_resets_checked": True,
            "scope": "Exhaustive Python event models and suffix oracle; SystemVerilog not HDL-simulated or physically timed."}


if __name__ == "__main__":
    result = verify()
    (ROOT / "checks/prep-043-verification.json").write_bytes(
        (json.dumps(result, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8"))
    print(json.dumps(result))
