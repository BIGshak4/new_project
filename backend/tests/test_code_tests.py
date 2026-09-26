"""Code tests: a candidate's Python runs against the question's cases, isolated, and never breaks the evaluation."""

from __future__ import annotations

import pytest

from app.engine import checks, code_runner

SPEC = {"type": "code_tests", "spec": {
    "language": "python", "timeout_ms": 3000, "entry": ["count_set_bits", "popcount"],
    "cases": [{"args": [0], "expected": 0}, {"args": [180], "expected": 4}, {"args": [4294967295], "expected": 32}]}}

GOOD = "Clear the lowest set bit until zero.\n\n```python\ndef count_set_bits(x):\n    n = 0\n    while x:\n        x &= x - 1\n        n += 1\n    return n\n```"
OFF_BY_ONE = "```python\ndef count_set_bits(x):\n    return sum((x >> i) & 1 for i in range(31))\n```"


class TestExtraction:
    def test_tagged_python_fence(self):
        assert code_runner.extract_python(GOOD).startswith("def count_set_bits")

    def test_untagged_fence_that_parses_is_python_and_c_is_not(self):
        assert code_runner.extract_python("```\ndef f(x):\n    return x\n```") == "def f(x):\n    return x"
        assert code_runner.extract_python("```text\ndef f(x):\n    return x\n```") is not None     # Harel's editor default tag
        assert code_runner.extract_python("```c\nint f(int x) { return x; }\n```") is None
        assert code_runner.extract_python("```c\nint f(int x) { return x; }\n```\nand in Python:\n```python\ndef f(x):\n    return x\n```") == "def f(x):\n    return x"

    def test_bare_python_and_prose(self):
        assert code_runner.extract_python("def f(x):\n    return x + 1") is not None
        assert code_runner.extract_python("I would loop over the bits and count the ones.") is None

    def test_two_blocks_are_joined(self):
        text = "```python\ndef helper(x):\n    return x & (x - 1)\n```\nthen\n```python\ndef count_set_bits(x):\n    n = 0\n    while x:\n        x = helper(x)\n        n += 1\n    return n\n```"
        assert checks.run_check(SPEC, text).passed is True


class TestAudit:
    @pytest.mark.parametrize("source", [
        "import os\ndef f(x):\n    return os.getpid()",
        "from subprocess import run\ndef f(x):\n    return 1",
        "def f(x):\n    return open('/etc/passwd').read()",
        "def f(x):\n    return eval('1')",
        "def f(x):\n    return ().__class__.__bases__[0].__subclasses__()",
        "def f(x):\n    return __import__('socket')",
    ])
    def test_dangerous_code_is_refused_before_running(self, source):
        assert code_runner.audit(source)
        result = checks.run_check(SPEC, f"```python\n{source}\n```")
        assert result.passed is None and "not run" in result.detail

    @pytest.mark.parametrize("source", [
        "def f(x):\n    return len.__self__.eval('1')",                      # the real builtins module via a method
        "def f(x):\n    return (lambda: 0).__globals__",
        "def f(x):\n    try:\n        1/0\n    except Exception as e:\n        return e.__traceback__.tb_frame",
        "def f(x):\n    return f.__code__",
    ])
    def test_attribute_routes_to_the_interpreter_are_refused(self, source):
        assert code_runner.audit(source)

    @pytest.mark.parametrize("source", [
        # operator.attrgetter / methodcaller resolve attribute names at run time, past the AST audit
        "import operator\ndef f(x):\n    return operator.methodcaller('__subclasses__')(object)",
        "from operator import attrgetter\ndef f(x):\n    return attrgetter('__init__.__globals__')(x)",
        "import string\ndef f(x):\n    return string.Formatter().get_field('0.__class__', [x], {})",
        "from typing import get_type_hints\ndef f(x):\n    return get_type_hints(f)",
        "import typing\ndef f(x):\n    return typing.get_type_hints(f)",
        "from math import *\ndef f(x):\n    return x",
    ])
    def test_run_time_attribute_lookups_are_refused(self, source):
        assert code_runner.audit(source)

    def test_child_process_sees_no_secrets(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://secret")
        env = code_runner.child_environment()
        assert "ANTHROPIC_API_KEY" not in env and "DATABASE_URL" not in env
        assert code_runner.run_in_subprocess("def f(x):\n    return x", {"cases": [{"args": [1], "expected": 1}]},
                                             timeout_seconds=20)["status"] == "ok"

    def test_allowed_imports_pass(self):
        assert code_runner.audit("import math\nfrom collections import deque\ndef f(x):\n    return math.gcd(x, 4)") == []

    def test_import_inside_the_function_is_also_blocked_at_run_time(self):
        source = "def count_set_bits(x):\n    m = __builtins__['__import__']('os')\n    return 0"
        result = checks.run_check(SPEC, f"```python\n{source}\n```")
        assert result.passed is None                                   # refused by the audit (__builtins__ name)
        outcome = code_runner.run_cases("def count_set_bits(x):\n    import os\n    return 0", SPEC["spec"])
        assert outcome["status"] == "ok" and all(not r["ok"] and "ImportError" in r["error"] for r in outcome["results"])


class TestRunning:
    def test_correct_code_passes(self):
        result = checks.run_check(SPEC, GOOD)
        assert result.passed is True and result.type == "code_tests" and "3 test cases" in result.detail
        assert result.mismatches == []

    def test_wrong_code_fails_with_the_differing_case(self):
        result = checks.run_check(SPEC, OFF_BY_ONE)
        assert result.passed is False and "1 of 3" in result.detail
        assert result.mismatches == [{"case": 2, "inputs": [4294967295], "expected": 32, "got": 31}]

    def test_no_python_is_not_checked(self):
        result = checks.run_check(SPEC, "```c\nint popcount(unsigned x) { int n = 0; while (x) { x &= x - 1; n++; } return n; }\n```")
        assert result.passed is None and "no Python" in result.detail
        assert checks.run_check(SPEC, "loop while x != 0, x &= x-1, count++").passed is None

    def test_exception_in_a_case_is_a_failure_with_the_error(self):
        result = checks.run_check(SPEC, "```python\ndef count_set_bits(x):\n    return 32 // x\n```")
        assert result.passed is False and result.mismatches[0]["error"].startswith("ZeroDivisionError")

    def test_infinite_loop_times_out(self):
        spec = {"type": "code_tests", "spec": {**SPEC["spec"], "timeout_ms": 1500}}
        result = checks.run_check(spec, "```python\ndef count_set_bits(x):\n    while True:\n        pass\n```")
        assert result.passed is False and "did not finish" in result.detail

    def test_entry_is_found_by_name_then_by_arity(self):
        by_alias = "```python\ndef popCount(v):\n    return bin(v).count('1')\n```"
        assert checks.run_check(SPEC, by_alias).passed is True
        by_arity = "```python\ndef helper(a, b):\n    return a + b\n\ndef bits(v):\n    return bin(v).count('1')\n```"
        assert checks.run_check(SPEC, by_arity).passed is True

    def test_tuples_generators_and_bools_compare_sensibly(self):
        spec = {"type": "code_tests", "spec": {"cases": [
            {"args": [[6, 6], 12], "accept": [[0, 1]], "unordered": True},
            {"args": [[6], 12], "accept": [None, [], -1]},
            {"args": [[1, 2], 3], "accept": [[0, 1]], "unordered": True}]}}
        code = ("```python\ndef pair(values, t):\n    seen = {}\n    for i, x in enumerate(values):\n"
                "        if t - x in seen:\n            return (i, seen[t - x])\n        seen[x] = i\n    return None\n```")
        assert checks.run_check(spec, code).passed is True
        gen = {"type": "code_tests", "spec": {"cases": [{"args": [3], "expected": [0, 1, 2]}]}}
        assert checks.run_check(gen, "```python\ndef f(n):\n    for i in range(n):\n        yield i\n```").passed is True
        truthy = {"type": "code_tests", "spec": {"cases": [{"args": [4], "expected": True}, {"args": [3], "expected": False}]}}
        assert checks.run_check(truthy, "```python\ndef f(x):\n    return x & (x - 1) == 0\n```").passed is True
        assert checks.run_check(truthy, "```python\ndef f(x):\n    return x % 2\n```").passed is False   # 0/1 the wrong way round

    def test_cases_do_not_leak_mutations_into_each_other(self):
        spec = {"type": "code_tests", "spec": {"cases": [{"args": [[3, 1, 2]], "expected": [1, 2, 3]},
                                                         {"args": [[3, 1, 2]], "expected": [1, 2, 3]}]}}
        code = "```python\ndef f(a):\n    a.sort()\n    return a\n```"
        assert checks.run_check(spec, code).passed is True

    def test_spec_without_cases_is_rejected_by_the_loader(self):
        with pytest.raises(ValueError):
            checks.run_check({"type": "code_tests", "spec": {"entry": ["f"]}}, GOOD)

    def test_in_process_and_isolated_runs_agree(self):
        isolated = checks.run_check(SPEC, GOOD)
        in_process = checks.run_check(SPEC, GOOD, sandbox=False)
        assert (isolated.passed, isolated.detail) == (in_process.passed, in_process.detail)


class TestThePool:
    """Code tests hold a thread for up to their timeout: they run in their own pool, never the default one."""

    SPEC = {"type": "code_tests", "spec": {"language": "python", "timeout_ms": 5000, "entry": ["count_set_bits"],
                                           "cases": [{"args": [0], "expected": 0}, {"args": [180], "expected": 4}]}}
    CODE = "def count_set_bits(x):\n    n = 0\n    while x:\n        x &= x - 1\n        n += 1\n    return n\n"

    async def test_same_result_in_the_code_test_pool(self, monkeypatch):
        import threading

        threads = []
        real = checks.run_check

        def spy(check, answer, **kwargs):
            threads.append(threading.current_thread().name)
            return real(check, answer, **kwargs)
        monkeypatch.setattr(checks, "run_check", spy)
        result = await checks.run_check_async(self.SPEC, self.CODE)
        direct = real(self.SPEC, self.CODE)
        assert result.model_dump(exclude={"runtime_ms"}) == direct.model_dump(exclude={"runtime_ms"})
        assert result.passed is True
        assert threads[0].startswith("code-tests")
        from pathlib import Path

        from app.engine.catalog import load_catalog
        truth = load_catalog(Path(__file__).resolve().parent.parent / "seeds").questions["example-sensor-majority"]
        await checks.run_check_async(truth.deterministic_check, "alarm = (A & B) | (A & C) | (B & C)")
        assert not threads[-1].startswith("code-tests")              # the quick checks stay in the default pool

    async def test_no_check_is_none(self):
        assert await checks.run_check_async(None, "anything") is None
