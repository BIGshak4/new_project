"""Independent finite checks for the four batch110 hardware-owned records."""

import importlib.util
import itertools
from fractions import Fraction
from pathlib import Path

SOLUTIONS = Path(__file__).resolve().parents[1] / "solutions"


def load(name):
    import sys

    spec = importlib.util.spec_from_file_location(name, SOLUTIONS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check191():
    m = load("prep_191_floor_log2_counter")
    for value in range(1 << 16):
        result, valid, cycles = m.floor_log2(value)
        if value:
            expected = max(i for i in range(16) if (1 << i) <= value)
            assert result == expected and valid
            assert (1 << result) <= value < (1 << (result + 1))
            assert cycles == expected + 1
        else:
            assert (result, valid, cycles) == (0, False, 0)
    d = m.FloorLog2Counter()
    d.tick(36, start=True)
    for count in range(1, 6):
        d.tick(65535, start=True)  # input changes and start are ignored while busy
        assert d.count == count
    assert d.tick(0) == {"result": 5, "busy": False, "done": True, "valid": True}
    assert not d.tick()["done"] and d.valid
    d.tick(65535, start=True)
    d.tick(reset=True)
    assert not d.busy and not d.valid and d.result == 0 and d.count == 0
    return {"status": "pass", "complete_unsigned_16_bit_domain": 65536,
                "directed_contract_checks": ["latency", "input snapshot", "busy start ignored",
                                          "done pulse", "synchronous reset", "zero invalid"],
                "scope": "Python clocked reference model; proposed SystemVerilog not compiled"}


def one_shot_oracle(inputs, duration, retriggerable, resets=()):
    # First identify every input edge; then construct accepted output intervals.
    edges = [t for t in range(len(inputs)) if inputs[t] and (t == 0 or not inputs[t-1])]
    reset_times = set(resets)
    intervals = []
    for edge in edges:
        if edge in reset_times:
            continue
        if intervals and edge < intervals[-1][1]:
            if retriggerable:
                intervals[-1][1] = edge + duration
            else:
                continue
        else:
            intervals.append([edge, edge + duration])
        future = [reset for reset in reset_times if edge < reset < intervals[-1][1]]
        if future:
            intervals[-1][1] = min(future)
    return [int(any(left <= t < right for left, right in intervals))
            for t in range(len(inputs))]


def check193():
    m = load("prep_193_monostable")
    count = 0
    for bits in itertools.product((0, 1), repeat=12):
        for duration in range(1, 6):
            for retriggerable in (False, True):
                assert m.waveform(bits, duration, retriggerable=retriggerable) == one_shot_oracle(
                    bits, duration, retriggerable)
                count += 1
    for bits in itertools.product((0, 1), repeat=8):
        for resets in ((0,), (2,), (3, 6), (0, 1, 2, 3)):
            for retriggerable in (False, True):
                assert m.waveform(bits, 3, retriggerable=retriggerable, resets=resets) == one_shot_oracle(
                    bits, 3, retriggerable, resets)
    pulse = [0, 1, 0, 1, 0, 0, 0, 0, 0]
    assert m.waveform(pulse) == [0, 1, 1, 1, 1, 0, 0, 0, 0]
    assert m.waveform(pulse, retriggerable=True) == [0, 1, 1, 1, 1, 1, 1, 0, 0]
    # Equal current Vin=0, unequal output: a static transfer curve is insufficient.
    assert m.waveform([0, 1, 0])[-1] == 1
    assert m.waveform([0, 0, 0])[-1] == 0
    return {"status": "pass", "exhaustive_12_sample_waveforms": count,
                "reset_waveform_cases": 2048,
                "scope": "Ideal integer-time behavioral model; no analog/SPICE or physical timing test"}


def check197():
    m = load("prep_197_four_wire_symbols")
    assert len({m.encode16(s) for s in range(16)}) == 16
    words = {m.encode18(s) for s in range(18)}
    assert len(words) == 18
    valid = 0
    for first in range(16):
        for second in range(16):
            expected = first + 16 * second
            try:
                actual = m.decode18(first, second)
            except ValueError:
                assert expected >= 18
            else:
                valid += 1
                assert actual == expected and m.encode18(actual) == (first, second)
    assert valid == 18
    assert (1 << 4) < 18 <= (1 << 5)
    assert 16 ** 1 < 18 <= 16 ** 2
    return {"status": "pass", "one_transfer_codes": 16, "framed_symbols": 18,
                "exhaustive_two_transfer_words": 256, "rejected_unassigned_words": 238,
                "scope": "Framed noiseless digital codec; no physical link or analog-level validation"}


def check073():
    m = load("prep_073_ninety_minute_bottles")
    groups = m.pools()
    patterns = set()
    for poisoned in range(1, 1001):
        dead = tuple(int(poisoned in group) for group in groups)
        assert m.identify(dead) == poisoned
        independent = tuple((poisoned - 1) // (2 ** bit) % 2 for bit in range(10))
        assert dead == independent
        patterns.add(dead)
        # Different allowed latencies never affect the endpoint mask.
        delays = [1 + ((poisoned * 17 + bit * 11) % 60) for bit in range(10)]
        observed = tuple(int(dead[bit] and delays[bit] <= 60) for bit in range(10))
        assert observed == dead
    assert len(patterns) == 1000 and m.identify([0] * 10) == 1
    for label in range(1000, 1024):
        try:
            m.identify([(label >> bit) & 1 for bit in range(10)])
        except ValueError:
            pass
        else:
            raise AssertionError("unused outcome accepted")
    for raw in ("0", "0.5", "29.999", "30", "59.999", "60", "60.001", "89.999", "90"):
        exposure = Fraction(raw)
        death = m.permitted_adversarial_death(exposure)
        assert 0 < death - exposure <= 60
        assert death == 60 if exposure < 60 else death > 90
    assert 2 ** 9 < 1000 <= 2 ** 10
    return {"status": "pass", "poisoned_bottle_cases": 1000, "unused_masks_rejected": 24,
                "bounded_delay_endpoint_cases": 1000, "adversarial_boundary_examples": 9,
                "scope": "Finite coding checks support the construction; adaptive timing lower bound is a separate proof, not exhaustive testing"}


CHECKS = {191: check191, 193: check193, 197: check197, 73: check073}
