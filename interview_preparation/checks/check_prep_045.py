"""Exhaustive sampled-input histories, independent history oracle and invariants."""
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("first_finisher", ROOT / "solutions/prep_045_first_finisher.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)
PULSES = tuple(itertools.product((0, 1), repeat=3))


def history_oracle(events):
    """Search the reset-delimited history for its first nonempty finish edge."""
    start = 0
    for index, (_, reset) in enumerate(events):
        if reset:
            start = index + 1
    arrivals = [(edge, lane + 1) for edge, (pulses, _) in enumerate(events[start:])
                for lane, active in enumerate(pulses) if active]
    return min(arrivals)[1] if arrivals else 0


def gate_equations(winner, pulses, reset):
    p1, p2, p3 = pulses
    high = (1 - p1) & (p2 | p3)
    low = p1 | ((1 - p2) & p3)
    candidate = 2 * high + low
    q1, q0 = (winner >> 1) & 1, winner & 1
    enable = 1 - (q1 | q0)
    return 0 if reset else candidate if enable else winner


def check_trace(events):
    register = MODEL.FirstFinisher()
    history = []
    for pulses, reset in events:
        old = register.winner
        history.append((pulses, reset))
        got = register.step(*pulses, reset=reset)
        assert got == history_oracle(history)
        assert got == gate_equations(old, pulses, reset)
        assert got in (0, 1, 2, 3)
        if reset:
            assert got == 0
        elif old:
            assert got == old


def verify():
    for winner, expected_enable in enumerate((1, 0, 0, 0)):
        assert 1 - (((winner >> 1) & 1) | (winner & 1)) == expected_enable
    transition_cases = 0
    for old, pulses, reset in itertools.product(range(4), PULSES, (False, True)):
        expected = (0 if reset else old if old else
                    min((i + 1 for i, active in enumerate(pulses) if active), default=0))
        assert MODEL.next_winner(old, *pulses, reset) == expected
        assert expected == gate_equations(old, pulses, reset)
        transition_cases += 1

    no_reset_streams = 0
    for length in range(7):
        for stream in itertools.product(PULSES, repeat=length):
            check_trace([(pulses, False) for pulses in stream])
            no_reset_streams += 1

    reset_streams = 0
    events = tuple(itertools.product(PULSES, (False, True)))
    for length in range(5):
        for stream in itertools.product(events, repeat=length):
            check_trace(stream)
            reset_streams += 1

    machine = MODEL.FirstFinisher()
    explicit = [(0, 0, 0), (0, 0, 1), (1, 0, 0), (0, 1, 0)]
    assert [machine.step(*p) for p in explicit] == [0, 3, 3, 3]
    assert machine.step(1, 1, 1, reset=True) == 0
    assert machine.step(0, 1, 1) == 2
    assert [machine.step(1, 1, 1) for _ in range(100)] == [2] * 100

    return {
        "question": "PREP-045", "status": "passed",
        "state_input_reset_combinations": transition_cases,
        "nor_enable_truth_rows": 4,
        "all_pulse_streams_lengths_0_to_6": no_reset_streams,
        "all_pulse_reset_streams_lengths_0_to_4": reset_streams,
        "locked_hold_cycles": 100,
        "oracle": "Independent history scan selects lexicographically earliest (edge, lane) after the latest reset.",
        "invariants": "Winner 0..3; reset dominates; any nonzero winner holds until reset; encoder Boolean equations agree.",
        "scope": "Python edge model and complete binary transition table, not HDL simulation, synthesis, CDC verification or physical button testing."
    }


if __name__ == "__main__":
    result = verify()
    (ROOT / "checks/prep-045-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
