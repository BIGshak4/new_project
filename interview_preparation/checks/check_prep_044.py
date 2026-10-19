"""Compare finite-width hardware model with exact fast-doubling Fibonacci."""
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fib_hw", ROOT / "solutions/prep_044_hardware_fibonacci.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def exact_fibonacci_pair(n):
    if n == 0:
        return 0, 1
    a, b = exact_fibonacci_pair(n // 2)
    c = a * (2 * b - a)
    d = a * a + b * b
    return (d, c + d) if n % 2 else (c, d)


def verify():
    samples = 0
    widths = tuple(range(1, 17)) + (17, 32, 64, 128)
    for width in widths:
        hardware = MODEL.FibonacciRegisters(width)
        modulus = 1 << width
        for k in range(513):
            expected_a, expected_b = exact_fibonacci_pair(k)
            assert hardware.value == expected_a % modulus
            assert hardware.b == expected_b % modulus
            samples += 1
            hardware.step()
    reset_traces = 0
    for width in range(1, 9):
        modulus = 1 << width
        for resets in itertools.product((False, True), repeat=10):
            hardware = MODEL.FibonacciRegisters(width)
            elapsed = 0
            for reset in resets:
                elapsed = 0 if reset else elapsed + 1
                expected_a, expected_b = exact_fibonacci_pair(elapsed)
                assert hardware.step(reset) == expected_a % modulus
                assert hardware.b == expected_b % modulus
            reset_traces += 1
    invalid_widths = 0
    for width in (0, -1, 1.5, True, "8", None):
        try:
            MODEL.FibonacciRegisters(width)
        except ValueError:
            invalid_widths += 1
        else:
            raise AssertionError("invalid width accepted")
    return {
        "question": "PREP-044", "status": "passed",
        "exact_fast_doubling_comparison_samples": samples,
        "widths": list(widths), "all_length_10_reset_traces_widths_1_to_8": reset_traces,
        "invalid_widths_rejected": invalid_widths,
        "scope": "Python clock-edge model and independent exact-number oracle. SystemVerilog supplied but not HDL-simulated, synthesized or physically timed."
    }


if __name__ == "__main__":
    report = verify()
    (ROOT / "checks/prep-044-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
