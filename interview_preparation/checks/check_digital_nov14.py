"""Run the six independent digital-logic models against behavioral oracles."""

import itertools
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "solutions"))
from prep_320_mux_layers import logical_right, mux4, mux8, xor
from prep_321_elevator_fsm import Elevator
from prep_322_byte_adapter import ByteAdapter
from prep_323_sampled_edges import EdgeDetector
from prep_324_divide_six import divide_six
from prep_325_pulse_width import PulseMeter


def test_mux():
    checks = 0
    for a, b in itertools.product(range(2), repeat=2):
        assert xor(a, b) == (a != b)
        checks += 1
    for width, circuit in ((4, mux4), (8, mux8)):
        for pins in itertools.product(range(2), repeat=width):
            for choice in range(width):
                assert circuit(choice, pins) == pins[choice]
                checks += 1
    for byte, offset in itertools.product(range(256), range(8)):
        assert logical_right(byte, offset) == byte >> offset
        checks += 1
    return checks


def test_elevator():
    cases = 0
    for start, cabin, hall in itertools.product(range(3), range(8), range(8)):
        elevator = Elevator()
        floor = start
        seen = []
        for time in range(32):
            state = elevator.state
            closed = state in ("idle", "travel", "closing")
            assert not elevator.motor(floor, False)
            movement = elevator.motor(floor, closed)
            assert not movement or state == "travel"
            floor += movement
            assert 0 <= floor <= 2
            elevator.tick(floor, closed, state == "opening",
                          cabin if time == 0 else 0, hall if time == 0 else 0)
            if elevator.state == "open":
                seen.append(floor)
        expected = [floor for floor in range(3) if (cabin | hall) & (1 << floor)]
        assert seen == expected and not elevator.pending and elevator.state == "idle"
        cases += 1
    e = Elevator()
    e.tick(0, True, False, cabin=4)
    e.tick(1, True, False, hall=1)
    assert e.target == 2 and e.pending == 5
    e.tick(2, True, False)
    e.tick(2, False, True, hall=6)
    assert e.pending == 3 and e.state == "open"
    e.tick(2, False, False, cabin=4)
    assert e.state == "closing" and e.pending == 7
    e.tick(2, False, False)
    assert e.state == "closing"
    e.tick(2, True, False)
    e.tick(2, True, False)
    assert e.target == 0
    return cases + 1


def test_link():
    link = ByteAdapter()
    for byte in range(256):
        assert link.tick(byte) is None
        pairs = [link.tick() for _ in range(4)]
        assert sum(value * (4 ** i) for i, value in enumerate(reversed(pairs))) == byte
    return 256


def test_edges():
    count = 0
    for bits in itertools.product(range(2), repeat=8):
        for reset_at in range(9):
            detector = EdgeDetector()
            last = 0
            for i, x in enumerate(bits):
                reset = i == reset_at
                expected = ((0, 0, 0) if reset else
                            (int(x > last), int(x < last), int(x != last)))
                assert detector.tick(x, reset) == expected
                last = 0 if reset else x
            count += 1
    return count


def test_divider():
    for byte in range(256):
        assert divide_six(byte) == divmod(byte, 6)
    return 256


def test_meter():
    checks = 0
    for n in list(range(1, 260)) + [500]:
        meter = PulseMeter()
        for run in (n, 1):
            assert not any(meter.tick(1) for _ in range(run))
            assert meter.tick(0)
            assert (meter.result, meter.overflow) == (min(run, 255), run > 255)
            assert not meter.tick(0)
        checks += 1
    meter = PulseMeter()
    meter.tick(1)
    assert not meter.tick(0, True)
    assert not meter.tick(0)
    return checks + 1


if __name__ == "__main__":
    results = {f"PREP-{n}": test() for n, test in enumerate(
        [test_mux, test_elevator, test_link, test_edges, test_divider, test_meter], 320)}
    print(json.dumps(results, indent=2))

