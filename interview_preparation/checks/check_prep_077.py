"""Exhaustive unsigned-byte models and identity/aliasing counterexamples."""

import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("swap", BANK / "solutions/prep_077_swap_without_temp.py")
solution = module_from_spec(spec)
spec.loader.exec_module(solution)


def run():
    pairs = 0
    for a in range(256):
        for b in range(256):
            assert solution.swap_u8_xor(a, b) == (b, a)
            assert solution.swap_u8_modular(a, b) == (b, a)
            assert solution.swap_exact(a, b) == (b, a)
            cells = [a, b]
            solution.swap_locations(cells, 0, 1)
            assert cells == [b, a]
            pairs += 1
    for value in range(256):
        cells = [value]
        solution.swap_locations(cells, 0, 0)
        assert cells == [value]
        damaged = value
        damaged ^= damaged
        assert damaged == 0  # first assignment already destroys aliased content
    for a, b in [(10**1000, -(10**900)), (0, 0), (-9, 7), (-2**100, -2**99)]:
        assert solution.swap_exact(a, b) == (b, a)
    result = {
        "question_id": "PREP-077", "checked_on": "2026-10-21", "status": "passed_python_models",
        "all_unsigned_byte_pairs": pairs, "algorithms_per_pair": 4, "alias_guard_values": 256,
        "large_or_signed_exact_integer_pairs": 4,
        "method": "Every pair 0..255 compared with the original reversed values for XOR, modulo-256 add/subtract, exact add/subtract and distinct-location updates. All 256 same-location calls verify identity and exhibit unguarded XOR destruction.",
        "limits": "Python models executed. Supplied C++ was not compiled; no compiler found. No signed-overflow execution, physical hardware or human expert review."
    }
    (BANK / "checks/prep-077-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
