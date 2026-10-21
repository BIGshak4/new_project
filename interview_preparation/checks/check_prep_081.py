"""Independent slice-sum oracles test exact block and sliding boundaries."""
import itertools
import json
import random
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_081_error_monitor import first_sliding_failure, fixed_block_results


def oracle_fixed(values, window, threshold):
    return ["Failed" if sum(values[start:start + window]) > threshold else "Passed"
            for start in range(0, len(values) - window + 1, window)]


def oracle_sliding(values, window, threshold):
    return next((t for t in range(len(values)) if sum(values[max(0, t - window + 1):t + 1]) > threshold), None)


def main():
    combinations = 0
    for length in range(11):
        for values in itertools.product((0, 1), repeat=length):
            for window in range(1, 7):
                for threshold in range(4):
                    assert fixed_block_results(values, window, threshold) == oracle_fixed(values, window, threshold)
                    assert first_sliding_failure(values, window, threshold) == oracle_sliding(values, window, threshold)
                    combinations += 1
    rng = random.Random(81021)
    for _ in range(2000):
        values = [rng.randrange(2) for _ in range(rng.randrange(200))]
        window, threshold = rng.randrange(1, 50), rng.randrange(16)
        assert fixed_block_results(values, window, threshold) == oracle_fixed(values, window, threshold)
        assert first_sliding_failure(values, window, threshold) == oracle_sliding(values, window, threshold)
    window = 100_000
    boundary_cases = []
    for events in (list(range(10)), list(range(11)), list(range(1, 11)) + [window], [0] + list(range(window - 10, window)),
                   list(range(window - 5, window + 6))):
        values = [0] * (2 * window)
        for event in events:
            values[event] = 1
        block = fixed_block_results(values)
        sliding = first_sliding_failure(values)
        assert block == oracle_fixed(values, window, 10)
        # Sparse event-index oracle avoids a quadratic 100000-wide slice sum.
        expected = next((events[k] for k in range(10, len(events)) if events[k] - events[k - 10] < window), None)
        assert sliding == expected
        boundary_cases.append({"event_cycles": events, "block_results": block, "first_sliding_failure": sliding})
    # Events at t=0 and t=100000 do not coexist in a 100000-cycle window.
    values = [0] * (window + 1)
    for event in [0] + list(range(window - 9, window + 1)):
        values[event] = 1
    assert first_sliding_failure(values) is None
    result = {"question_id": "PREP-081", "status": "passed", "exhaustive_sequence_window_threshold_cases": combinations,
              "seeded_random_cases": 2000, "full_100000_cycle_boundary_cases": boundary_cases,
              "expiration_at_exact_window_age": "passed", "scope": "Python cycle-sampled binary sequence verification; not physical sampling, CDC, or simulator integration."}
    (BANK / "checks/prep-081-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
