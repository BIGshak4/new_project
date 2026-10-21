"""Independent trial division and known prime-counting checkpoints."""

import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("sieve", BANK / "solutions/prep_080_count_primes_sieve.py")
solution = module_from_spec(spec)
spec.loader.exec_module(solution)


def is_prime(n):
    if n < 2:
        return False
    divisor = 2
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 1
    return True


def run():
    expected = 0
    for n in range(2001):
        expected += is_prime(n)
        assert solution.count_primes(n) == expected
    checkpoints = {10: 4, 100: 25, 1000: 168, 10000: 1229, 100000: 9592}
    for n, count in checkpoints.items():
        assert solution.count_primes(n) == count
    for invalid in (-1, True, 3.0, "10", None):
        try:
            solution.count_primes(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(invalid)
    result = {
        "question_id": "PREP-080", "checked_on": "2026-10-21", "status": "passed_python_code",
        "inclusive_endpoints_against_trial_division": 2001, "checkpoints": checkpoints,
        "invalid_input_rejections": 5,
        "method": "Independent divisibility oracle for every upper endpoint 0..2000, plus five standard prime-count checkpoints through 100000. Includes prime squares, 0,1,2 and inclusive endpoint handling.",
        "limits": "Finite deterministic tests, not a performance benchmark or a proof of global fastest prime-counting algorithm. No giant allocation tests or human professional review."
    }
    (BANK / "checks/prep-080-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
