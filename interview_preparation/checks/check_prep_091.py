"""Exhaustive ideal event traces vs an independently retained input sample."""
import itertools
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_091_async_change_pulse import ChangePulse


def main():
    cases = steps = 0
    actions = ("rise", "zero", "one")
    for length in range(9):
        for trace in itertools.product(actions, repeat=length):
            for initial in (0, 1):
                model = ChangePulse(initial, initial)
                current = remembered = initial
                for action in trace:
                    if action == "rise":
                        remembered = current
                        observed = model.rising_edge()
                    else:
                        current = int(action == "one")
                        observed = model.input_change(current)
                    assert observed == int(current != remembered)
                    steps += 1
                cases += 1
    model = ChangePulse()
    named = [("rise", 0), ("one", 1), ("rise", 0), ("rise", 0),
             ("zero", 1), ("rise", 0), ("rise", 0)]
    for action, expected in named:
        actual = model.rising_edge() if action == "rise" else model.input_change(int(action == "one"))
        assert actual == expected
    result = {"question_id": "PREP-091", "status": "passed", "traces": cases,
              "event_checks": steps, "source_waveform_event_checks": len(named),
              "scope": "Ideal binary event model only; no HDL, synthesis, STA or metastability validation."}
    (BANK / "checks/prep-091-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
