"""Exhaustive address/SIZE truth table and counted single incrementer use."""

import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "address145", BANK / "solutions/prep_145_address_size_single_incrementer.py"
)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    calls = valid_cases = invalid_cases = carry_cases = 0
    for address in range(256):
        for size in range(8):

            def increment(value):
                nonlocal calls
                calls += 1
                assert 0 <= value <= 255
                # Independent binary toggle chain for the functional +1 block.
                bits = [(value >> bit) & 1 for bit in range(8)]
                carry = 1
                for i, bit in enumerate(bits):
                    bits[i], carry = bit ^ carry, bit & carry
                return sum(bit << i for i, bit in enumerate(bits))

            before = calls
            valid, result = model.address_plus_size(address, size, incrementer=increment)
            assert calls == before + 1
            assert valid == (size in (1, 2, 4))
            assert 0 <= result <= 511
            if valid:
                assert result == address + size
                valid_cases += 1
                carry_cases += result >= 256
            else:
                assert result == 0
                invalid_cases += 1
    rejected = 0
    for address, size in ((-1, 1), (256, 1), (True, 1), (0, -1), (0, 8), (0, True)):
        try:
            model.address_plus_size(address, size)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError((address, size))
    return {
        "question_id": "PREP-145",
        "status": "passed",
        "valid_address_size_cases": valid_cases,
        "invalid_size_rows": invalid_cases,
        "single_incrementer_calls": calls,
        "ninth_bit_carry_cases": carry_cases,
        "malformed_port_values_rejected": rejected,
        "scope": "All 2048 legal port bit patterns checked; 768 valid arithmetic cases compared with integer addition. One counted functional incrementer per row. No physical gate count, HDL or timing verification.",
    }


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-145-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))
