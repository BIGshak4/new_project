"""Run a candidate's Python against a question's test cases.

This module is self-contained on purpose: it is also the script a separate, isolated
interpreter runs (`python -I -S code_runner.py`), so it must not import anything from `app`.

Two layers keep a candidate's code from doing harm:
  1. `audit()` walks the AST and refuses imports outside a small allow-list, dangerous
     built-ins (open, exec, eval, __import__ ...) and introspection attributes
     (__subclasses__, __globals__ ...) before anything runs;
  2. the code runs in a child interpreter with isolated flags, a restricted set of
     built-ins, a wall-clock timeout enforced by the parent, and, where the platform
     allows, memory and CPU limits.
The self-tests of our own seed answers run in-process (`run_cases`) through the very
same harness, so what the loader validates is what candidates get.
"""

from __future__ import annotations

import ast
import builtins
import contextlib
import importlib
import inspect
import itertools
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ALLOWED_MODULES = {"math", "itertools", "collections", "functools", "typing", "heapq", "bisect", "string", "re",
                   "dataclasses", "operator", "fractions", "decimal", "enum", "abc", "array", "copy", "numbers"}
DENIED_NAMES = {"open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars", "getattr", "setattr",
                "delattr", "breakpoint", "input", "exit", "quit", "help", "memoryview", "__builtins__", "__loader__",
                "__spec__"}
DENIED_ATTRS = {"__subclasses__", "__globals__", "__builtins__", "__class__", "__bases__", "__mro__", "__code__",
                "__closure__", "__dict__", "__reduce__", "__reduce_ex__", "__getattribute__", "__getattr__",
                "__import__", "__loader__", "__spec__", "__self__", "__func__", "__wrapped__", "__objclass__",
                "__init_subclass__", "__traceback__", "__context__", "__cause__", "f_back", "f_globals", "f_locals",
                "f_builtins", "f_code", "gi_frame", "gi_code", "cr_frame", "cr_code", "ag_frame", "ag_code",
                "tb_frame", "tb_next"} | DENIED_NAMES          # len.__self__ is the real builtins module: no route to it
SAFE_BUILTINS = ["abs", "all", "any", "bin", "bool", "bytearray", "bytes", "callable", "chr", "complex", "dict",
                 "divmod", "enumerate", "filter", "float", "format", "frozenset", "hash", "hex", "id", "int",
                 "isinstance", "issubclass", "iter", "len", "list", "map", "max", "min", "next", "object", "oct",
                 "ord", "pow", "range", "repr", "reversed", "round", "set", "slice", "sorted", "str", "sum", "super",
                 "tuple", "type", "zip", "staticmethod", "classmethod", "property", "NotImplemented", "Ellipsis",
                 "Exception", "BaseException", "ArithmeticError", "AssertionError", "AttributeError", "IndexError",
                 "KeyError", "LookupError", "NotImplementedError", "OverflowError", "RecursionError", "RuntimeError",
                 "StopIteration", "TypeError", "ValueError", "ZeroDivisionError"]

MAX_ITEMS = 10_000                  # how much of an iterator result is materialised
MAX_REPR = 300                      # how long a reported value may be
DEFAULT_TIMEOUT_MS = 5000

_FENCE_RE = re.compile(r"(`{3,})[ \t]*([\w+#.-]*)[^\n]*\n(.*?)\n\1", re.DOTALL)
_PYTHON_TAGS = {"python", "py", "python3"}
_UNTAGGED = {"", "text", "pseudo", "pseudocode", "code", "txt"}


# ----------------------------------------------------------------------------- finding the code

def _parses(source: str) -> bool:
    try:
        ast.parse(source)
    except (SyntaxError, ValueError):
        return False
    return True


def extract_python(text: str) -> str | None:
    """The Python in a free-text answer: tagged fences first, untagged fences that parse, else the whole text.

    Fences tagged with another language (c, verilog, javascript ...) are never treated as Python.
    Several Python blocks are joined: candidates often split a helper from the main function.
    """
    blocks, untagged = [], []
    for match in _FENCE_RE.finditer(text):
        tag, body = match.group(2).lower(), match.group(3)
        if tag in _PYTHON_TAGS:
            blocks.append(body)
        elif tag in _UNTAGGED and "def " in body and _parses(body):
            untagged.append(body)
    chosen = blocks or untagged
    if chosen:
        return "\n\n".join(chosen)
    stripped = text.strip()
    if "def " in stripped and _parses(stripped):
        return stripped
    return None


def audit(source: str) -> list[str]:
    """Why the code must not run, or an empty list."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError) as exc:
        return [f"syntax error: {exc}"]
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_MODULES:
                    problems.append(f"import of {alias.name} is not allowed")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_MODULES or node.level:
                problems.append(f"import from {node.module or '.'} is not allowed")
        elif isinstance(node, ast.Name) and node.id in DENIED_NAMES:
            problems.append(f"use of {node.id} is not allowed")
        elif isinstance(node, ast.Attribute) and node.attr in DENIED_ATTRS:
            problems.append(f"access to {node.attr} is not allowed")
    return sorted(set(problems))


# ----------------------------------------------------------------------------- running it

def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name.split(".")[0] not in ALLOWED_MODULES:
        raise ImportError(f"import of {name} is not allowed here")
    return importlib.__import__(name, globals, locals, fromlist, level)


def _safe_builtins() -> dict:
    safe = {name: getattr(builtins, name) for name in SAFE_BUILTINS if hasattr(builtins, name)}
    safe["__import__"] = _restricted_import
    safe["print"] = lambda *args, **kwargs: None          # output is not part of the result
    safe["True"], safe["False"], safe["None"] = True, False, None
    return safe


def _normalize(value, depth: int = 0):
    """Tuples and iterators become lists, sets sorted lists, so [0, 1] and (0, 1) compare equal."""
    if depth > 6:
        return value
    if isinstance(value, bool) or value is None or isinstance(value, (int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): _normalize(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        try:
            return sorted(_normalize(v, depth + 1) for v in value)
        except TypeError:
            return [_normalize(v, depth + 1) for v in value]
    if isinstance(value, (list, tuple)):
        return [_normalize(v, depth + 1) for v in value]
    if hasattr(value, "__iter__"):
        return [_normalize(v, depth + 1) for v in itertools.islice(value, MAX_ITEMS)]
    return repr(value)[:MAX_REPR]


def _matches(got, case: dict) -> bool:
    wanted = case["accept"] if "accept" in case else [case.get("expected")]
    for want in wanted:
        want = _normalize(want)
        candidate = got
        if case.get("unordered") and isinstance(candidate, list) and isinstance(want, list):
            with contextlib.suppress(TypeError):
                candidate, want = sorted(candidate), sorted(want)
        if isinstance(want, bool):
            if isinstance(candidate, (bool, int)) and not isinstance(candidate, float) and bool(candidate) == want \
                    and candidate in (0, 1):
                return True
            continue
        if isinstance(want, float) and isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
            if abs(candidate - want) <= case.get("tolerance", 1e-9) * max(1.0, abs(want)):
                return True
            continue
        if candidate == want and type(candidate) is not bool or (candidate == want and isinstance(want, bool)):
            return True
    return False


def _canonical(name: str) -> str:
    return name.lower().replace("_", "")


def find_entry(namespace: dict, spec: dict, first_args: list):
    """The function to test: a named entry point, else the only function, else the last one with the right arity."""
    functions = [(name, obj) for name, obj in namespace.items()
                 if inspect.isfunction(obj) and not name.startswith("_")]
    wanted = [_canonical(n) for n in spec.get("entry", [])]
    for want in wanted:
        for name, obj in functions:
            if _canonical(name) == want:
                return obj
    if len(functions) == 1:
        return functions[0][1]
    fitting = []
    for _name, obj in functions:
        try:
            params = [p for p in inspect.signature(obj).parameters.values()
                      if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        except (TypeError, ValueError):
            continue
        required = sum(1 for p in params if p.default is p.empty)
        if required <= len(first_args) <= len(params):
            fitting.append(obj)
    if fitting:
        return fitting[-1]
    return functions[-1][1] if functions else None


def _short(value) -> object:
    text = json.dumps(value, ensure_ascii=False, default=repr)
    return value if len(text) <= MAX_REPR else text[:MAX_REPR] + "…"


def run_cases(source: str, spec: dict) -> dict:
    """Execute the source and call its entry point on every case. Never raises for candidate mistakes."""
    cases = spec.get("cases") or []
    namespace = {"__builtins__": _safe_builtins(), "__name__": "candidate"}
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(min(old_limit, 1500))
    try:
        try:
            exec(compile(source, "<candidate>", "exec"), namespace)     # noqa: S102 - audited, sandboxed candidate code
        except BaseException as exc:                                 # noqa: BLE001 - anything the candidate raises
            return {"status": "raised", "error": _describe(exc), "results": []}
        entry = find_entry(namespace, spec, list(cases[0].get("args", [])) if cases else [])
        if entry is None:
            return {"status": "no_entry", "error": "no function was defined", "results": []}
        results = []
        for index, case in enumerate(cases):
            args, kwargs = list(case.get("args", [])), dict(case.get("kwargs", {}))
            item = {"case": index, "inputs": _short(args if not kwargs else {"args": args, "kwargs": kwargs}),
                    "expected": _short(case["accept"][0] if "accept" in case else case.get("expected"))}
            try:
                got = _normalize(entry(*_copy(args), **kwargs))
            except BaseException as exc:                             # noqa: BLE001
                item.update(ok=False, error=_describe(exc))
            else:
                item.update(ok=_matches(got, case), got=_short(got))
            results.append(item)
        return {"status": "ok", "entry": getattr(entry, "__name__", "?"), "results": results}
    finally:
        sys.setrecursionlimit(old_limit)


def _copy(args: list) -> list:
    return json.loads(json.dumps(args))       # a fresh copy per call: in-place mutation must not leak between cases


def _describe(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {str(exc)[:200]}"


def _limit_resources() -> None:
    try:
        import resource
    except ImportError:                        # Windows
        return
    for kind, value in (("RLIMIT_AS", 512 * 1024 * 1024), ("RLIMIT_CPU", 10), ("RLIMIT_NPROC", 16),
                        ("RLIMIT_FSIZE", 1024 * 1024)):
        if hasattr(resource, kind):
            with contextlib.suppress(ValueError, OSError):
                resource.setrlimit(getattr(resource, kind), (value, value))


def child_environment() -> dict[str, str]:
    """The child gets no secrets: only what an interpreter needs to start on this platform."""
    keep = ("SYSTEMROOT", "PATH", "TEMP", "TMP", "TMPDIR", "LANG", "LC_ALL", "HOME", "USERPROFILE")
    return {key: os.environ[key] for key in keep if key in os.environ}


def run_in_subprocess(source: str, spec: dict, *, timeout_seconds: float) -> dict:
    """Run the cases in an isolated child interpreter; the parent enforces the wall-clock timeout."""
    payload = json.dumps({"source": source, "spec": spec})
    command = [sys.executable, "-I", "-S", "-X", "utf8", str(Path(__file__).resolve())]
    try:
        completed = subprocess.run(command, input=payload, capture_output=True, text=True, encoding="utf-8",
                                   timeout=timeout_seconds, check=False, env=child_environment(),
                                   cwd=tempfile.gettempdir())
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "error": f"did not finish within {timeout_seconds:g} s", "results": []}
    except OSError as exc:
        return {"status": "unavailable", "error": f"could not start the runner: {exc}", "results": []}
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        return {"status": "crashed", "error": (completed.stderr or "").strip()[-300:] or "runner produced no result",
                "results": []}
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {"status": "crashed", "error": "runner produced an unreadable result", "results": []}


def main() -> None:
    _limit_resources()
    payload = json.loads(sys.stdin.read())
    result = run_cases(payload["source"], payload["spec"])
    sys.stdout.write(json.dumps(result, ensure_ascii=False, default=repr) + "\n")


if __name__ == "__main__":
    main()
