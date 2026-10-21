"""Independent enumeration of every nonempty interval, including tie order."""
import importlib.util
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prep072", ROOT / "solutions/prep_072_maximum_subarray.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def oracle(values):
    intervals = [(sum(values[i:j+1]), i, j) for i in range(len(values)) for j in range(i, len(values))]
    return min(intervals, key=lambda t: (-t[0], t[1], t[2])) if intervals else None


def main():
    count = 0
    for length in range(8):
        for values in itertools.product(range(-2, 3), repeat=length):
            actual = model.maximum_subarray(values)
            assert actual == oracle(values), (values, actual, oracle(values))
            count += 1
    rng = random.Random(7201)
    for _ in range(500):
        values = [rng.randrange(-(10**60), 10**60) for _ in range(rng.randrange(1, 31))]
        assert model.maximum_subarray(values) == oracle(values)
    literal = [1, -4, -2, 5, 1, 0, -5, 4, 1, -3, -3]
    displayed_claim = 7
    actual = model.maximum_subarray(literal)
    assert actual == (6, 3, 4) and actual[0] != displayed_claim
    cases = [[], [-5], [-5, -2, -9], [0, 0], [1, -1, 1], [-2, 1, -3, 4, -1, 2, 1, -5, 4], literal]
    report = {"question_id": "PREP-072", "checked_on": "2026-10-21", "status": "passed_python_code",
              "exhaustive_arrays": count, "exhaustive_domain": "All lengths 0..7 over integers -2..2",
              "seeded_large_integer_arrays": 500,
              "oracle": "Enumerate every nonempty [i,j], compute sum by direct summation and select maximum sum then earliest start/end.",
              "examples": [{"values": values, "result": model.maximum_subarray(values)} for values in cases],
              "source_ambiguity": {"candidate_ltr_transcription": literal, "candidate_result": actual, "source_claim": displayed_claim,
                                   "note": "Bidirectional screenshot transcription is uncertain. The candidate ASCII transcription gives six, not seven; source is preserved, no silent correction or fabricated match."},
              "scope": "Executed Python implementation, exhaustive finite inputs plus seeded larger integers. This verifies cases, not the asymptotic proof or independent human approval."}
    (ROOT / "checks/prep-072-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
