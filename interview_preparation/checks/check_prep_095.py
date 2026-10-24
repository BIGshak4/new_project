"""Sliding history monitor checked against independent explicit suffix sums."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_095_sliding_window_monitor import WindowMonitor, check_samples


def main():
    cases = steps = detected = 0
    for length in range(15):
        for values in itertools.product((0, 1), repeat=length):
            expected = [int(sum(values[max(0, i - 9):i + 1]) >= 3) for i in range(length)]
            model = WindowMonitor()
            actual = [model.sample(x) for x in values]
            assert actual == expected
            assert check_samples(values, expected) == []
            for i in (0, length // 2, length - 1):
                if 0 <= i < length:
                    wrong = expected.copy()
                    wrong[i] ^= 1
                    assert check_samples(values, wrong) == [i]
                    detected += 1
            model.reset()
            assert model.history == 0 and model.sample(0) == 0
            steps += length
            cases += 1
    # Third high is included immediately; the first expires at sample 11.
    values = [1, 0, 1, 0, 1] + [0] * 10
    expected = [0] * 4 + [1] * 6 + [0] * 5
    assert check_samples(values, expected) == []
    for bad in (-1, 2, None):
        try:
            WindowMonitor().sample(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("nonbinary value accepted")
    try:
        check_samples([0], [])
    except ValueError:
        pass
    else:
        raise AssertionError("length mismatch accepted")
    result = {"question_id": "PREP-095", "status": "passed", "streams": cases,
              "sample_checks": steps, "single_cycle_corruptions_detected": detected,
              "scope": "Python sampled-cycle monitor and checker; no simulator, DUT or physical hardware tested."}
    (BANK / "checks/prep-095-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
