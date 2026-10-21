"""Enumerate sampled input/reset sequences against an event-list oracle."""
import itertools
import json
import random
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_078_fifth_rise import EveryFifthRise


def compare(trace):
    dut = EveryFifthRise()
    observed = []
    highs = []
    previous = 0
    for cycle, (signal, reset) in enumerate(trace):
        if reset:
            previous, highs = 0, []
            expected = 0
        else:
            if signal and not previous:
                highs.append(cycle)
            expected = int(bool(highs) and highs[-1] == cycle and len(highs) % 5 == 0)
            previous = signal
        actual = dut.tick(signal, reset)
        assert actual == expected
        assert dut.count == len(highs) % 5
        assert dut.previous == previous
        observed.append(actual)
    return observed


def main():
    seqs = cycles = 0
    for length in range(13):
        for values in itertools.product((0, 1), repeat=length):
            compare([(v, False) for v in values])
            seqs += 1
            cycles += length
    reset_traces = 0
    for choices in itertools.product(range(4), repeat=7):
        compare([(v & 1, bool(v & 2)) for v in choices])
        reset_traces += 1
    rng = random.Random(78021)
    random_traces = 200
    for _ in range(random_traces):
        compare([(rng.randrange(2), rng.random() < .025) for _ in range(1000)])
    long_high = compare([(0, False)] + [(1, False)] * 100)
    assert not any(long_high)
    example_input = [0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0]
    example = compare([(x, False) for x in example_input])
    assert [i for i, p in enumerate(example) if p] == [10]
    result = {"question_id": "PREP-078", "status": "passed", "exhaustive_input_sequences": seqs,
              "input_sequence_cycles": cycles, "exhaustive_reset_sequences_length_7": reset_traces,
              "seeded_random_traces": random_traces, "cycles_per_random_trace": 1000,
              "long_high_counts_once": True, "example_samples": example_input, "example_pulses": example,
              "scope": "Python discrete clock-edge model only; supplied SystemVerilog not compiled or HDL-simulated; no CDC or physical timing verification."}
    (BANK / "checks/prep-078-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
