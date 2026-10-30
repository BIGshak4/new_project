"""Enumerate initial memory states; verify the interface trace and exact cost."""
import importlib.util
import json
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("circular_length", BANK / "solutions/prep_178_unknown_circular_memory.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def verify():
    checked = 0
    for size in range(1, 13):
        for initial in product((0, 1), repeat=size):
            memory = model.CircularBits(initial)
            trace = []

            def write(address, bit, _trace=trace, _memory=memory):
                _trace.append(("write", address, bit))
                _memory.write(address, bit)

            def read(address, _trace=trace, _memory=memory):
                value = _memory.read(address)
                _trace.append(("read", address, value))
                return value

            assert model.discover_length(read, write) == size
            assert memory.reads == size and memory.writes == size + 1
            assert trace[0] == ("write", 0, 1)
            assert [row[2] for row in trace if row[0] == "read"] == [1] * (size - 1) + [0]
            checked += 1
    for size in (13, 31, 64, 127, 1000):
        for initial in ([0] * size, [1] * size, [i % 2 for i in range(size)]):
            memory = model.CircularBits(initial)
            assert model.discover_length(memory.read, memory.write) == size
            checked += 1
    return {"status": "passed", "enumerated_initial_states": 8190, "additional_cases": 15,
            "cases": checked, "domain": "All bit patterns at each size 1..12, plus five larger sizes and three initial patterns.",
            "cost": "N reads + N+1 writes, independent of initial bits",
            "limitations": "Destructive abstract Python interface model; no physical RAM, concurrency or address-overflow test."}


if __name__ == "__main__":
    result = verify()
    Path(__file__).with_name("prep-178-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
