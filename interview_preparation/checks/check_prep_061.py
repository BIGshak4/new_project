"""Independent fast-doubling oracle and call-count check for Fibonacci."""
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

BANK = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("fib_software", BANK / "solutions/prep_061_fibonacci_software.py")
solution = module_from_spec(spec)
spec.loader.exec_module(solution)


def oracle_pair(n):
    if n == 0:
        return 0, 1
    a, b = oracle_pair(n // 2)
    c = a * (2 * b - a)
    d = a*a + b*b
    return (d, c + d) if n % 2 else (c, d)


def count_actual_naive(n):
    calls = 0
    def profile(frame, event, arg):
        nonlocal calls
        if event == "call" and frame.f_code.co_name == "fib":
            calls += 1
    previous = sys.getprofile()
    try:
        sys.setprofile(profile)
        result = solution.fibonacci_recursive(n)
    finally:
        sys.setprofile(previous)
    return result, calls


def run():
    counts = {}
    for name, bound in (("fibonacci_recursive", 24), ("fibonacci_memoized", 200), ("fibonacci_iterative", 1000)):
        fn = getattr(solution, name)
        for n in range(bound + 1):
            assert fn(n) == oracle_pair(n)[0]
        counts[name] = bound + 1
    callchecks = 0
    for n in range(25):
        result, calls = count_actual_naive(n)
        assert result == oracle_pair(n)[0]
        assert calls == 2 * oracle_pair(n+1)[0] - 1
        callchecks += 1
    large = []
    for n in (2000, 10000):
        value = solution.fibonacci_iterative(n)
        assert value == oracle_pair(n)[0]
        large.append({"n":n, "result_bits":value.bit_length()})
    invalid = 0
    for name in counts:
        for arg in (-1, -100, True, False, 2.0, None, "3"):
            try:
                getattr(solution,name)(arg)
            except ValueError:
                invalid += 1
            else:
                raise AssertionError((name,arg))
    result = dict(question_id="PREP-061",checked_on="2026-10-21",status="passed_python_model",
                  oracle_cases=counts, naive_call_count_cases=callchecks, large_exact_cases=large,
                  rejected_inputs=invalid,
                  method="Compare three implementations against an independent fast-doubling oracle; check exact naive call count 2*F(n+1)-1.",
                  limits="No wall-clock asymptotic benchmark; recursion limited to modest n. Complexity distinguishes arithmetic counts from arbitrary-precision bit cost. No human expert approval.")
    (BANK / "checks/prep-061-verification.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    run()
