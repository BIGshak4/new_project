"""Check a two-bit enable/direction variant against arithmetic, not the old interface."""
import importlib.util
import json
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("two_bit_counter", BANK / "solutions/prep_064_two_bit_enable_direction_batch90.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def oracle(state, enable, direction, reset=0):
    return 0 if reset else (state + (-1 if direction else 1)) % 4 if enable else state


def verify():
    transitions = 0
    for state, enable, direction, reset in product(range(4), (0, 1), (0, 1), (0, 1)):
        assert model.next_state(state, enable, direction, reset) == oracle(state, enable, direction, reset)
        transitions += 1
    sequences = 0
    controls = tuple(product((0, 1), repeat=2))
    for length in range(7):
        for sequence in product(controls, repeat=length):
            for initial in range(4):
                actual = expected = initial
                for enable, direction in sequence:
                    actual = model.next_state(actual, enable, direction)
                    expected = oracle(expected, enable, direction)
                    assert actual == expected
                sequences += 1
    return {"status": "passed", "transitions_with_reset": transitions, "sequences": sequences,
            "domain": "All four states, binary enable/direction/reset; all control sequences at lengths0..6 from every state.",
            "interface": "inc=enable, dec=direction (1down,0up); inc0 holds even if dec1",
            "limitations": "Synchronous logical Python model, no HDL synthesis or timing simulation."}


if __name__ == "__main__":
    result = verify()
    Path(__file__).with_name("prep-064-two-bit-batch90-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
