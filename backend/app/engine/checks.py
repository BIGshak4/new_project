"""Deterministic checks (Data_Models §13.4).

A check result is an INPUT to the evaluator, not a replacement for it: a failed
truth table caps correctness, a pass raises the floor, and the rubric still scores
reasoning (AI_Engine_Spec §2.3).

Nothing here uses eval(): Boolean expressions go through a small parser so a
candidate's answer can never execute code in this process. Code tests are the one
check that runs a candidate's code, and they do it in an audited, isolated child
interpreter (see code_runner.py).
"""

from __future__ import annotations

import itertools
import re
import time

from app.engine import code_runner
from app.schemas.engine import CheckResult

# ----------------------------------------------------------------------------- boolean parser


class BooleanParseError(ValueError):
    pass


# Untrusted input: bound the work before parsing, so no answer can exhaust the stack.
MAX_EXPRESSION_LENGTH = 2000
MAX_NESTING_DEPTH = 32


_TOKEN_RE = re.compile(
    r"\s*(?:(?P<const>[01])|(?P<ident>[A-Za-z_][A-Za-z_0-9]*)|(?P<op>\(|\)|~|!|'|&&|&|\*|·|∧|\|\||\||\+|∨|\^|⊕))"
)

_AND_OPS = {"&", "&&", "*", "·", "∧"}
_OR_OPS = {"|", "||", "+", "∨"}
_XOR_OPS = {"^", "⊕"}
_NOT_PREFIX = {"~", "!"}
_WORD_OPS = {"and": "&", "or": "|", "xor": "^", "not": "~"}


def _tokenize(text: str, variables: list[str]) -> list[str]:
    single_letter = all(len(v) == 1 for v in variables)
    known = set(variables)
    tokens: list[str] = []
    pos = 0
    text = text.strip()
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m or m.end() == pos:
            raise BooleanParseError(f"unexpected character {text[pos]!r} at position {pos}")
        pos = m.end()
        if m.group("const") is not None:
            tokens.append(m.group("const"))
        elif m.group("ident") is not None:
            ident = m.group("ident")
            if ident.lower() in _WORD_OPS:
                tokens.append(_WORD_OPS[ident.lower()])
            elif ident in known:
                tokens.append(ident)
            elif single_letter and all(ch in known for ch in ident):
                tokens.extend(ident)               # "AB" means A AND B when every variable is one letter
            else:
                raise BooleanParseError(f"unknown variable {ident!r}")
        else:
            tokens.append(m.group("op"))
    return tokens


class _Parser:
    """Precedence: NOT > AND (explicit or by adjacency) > XOR > OR."""

    def __init__(self, tokens: list[str], variables: list[str]):
        self.tokens = tokens
        self.pos = 0
        self.variables = set(variables)
        self.depth = 0

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _take(self) -> str:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse(self):
        node = self._or()
        if self._peek() is not None:
            raise BooleanParseError(f"unexpected token {self._peek()!r}")
        return node

    def _or(self):
        node = self._xor()
        while self._peek() in _OR_OPS:
            self._take()
            node = ("or", node, self._xor())
        return node

    def _xor(self):
        node = self._and()
        while self._peek() in _XOR_OPS:
            self._take()
            node = ("xor", node, self._and())
        return node

    def _starts_operand(self, tok: str | None) -> bool:
        return tok is not None and (tok in self.variables or tok in {"0", "1", "("} or tok in _NOT_PREFIX)

    def _and(self):
        node = self._not()
        while True:
            tok = self._peek()
            if tok in _AND_OPS:
                self._take()
                node = ("and", node, self._not())
            elif self._starts_operand(tok):        # adjacency: A B, A(B+C), AB'
                node = ("and", node, self._not())
            else:
                return node

    def _not(self):
        # count complements iteratively so "~~~~A" or "A''''" cannot recurse; pairs cancel out
        negations = 0
        while self._peek() in _NOT_PREFIX:
            self._take()
            negations += 1
        node = self._atom()
        while self._peek() == "'":                 # postfix complement: A'
            self._take()
            negations += 1
        return ("not", node) if negations % 2 else node

    def _atom(self):
        tok = self._peek()
        if tok is None:
            raise BooleanParseError("unexpected end of expression")
        if tok == "(":
            self._take()
            self.depth += 1
            if self.depth > MAX_NESTING_DEPTH:
                raise BooleanParseError(f"more than {MAX_NESTING_DEPTH} nested parentheses")
            node = self._or()
            self.depth -= 1
            if self._peek() != ")":
                raise BooleanParseError("missing closing parenthesis")
            self._take()
            return node
        if tok in {"0", "1"}:
            self._take()
            return ("const", tok == "1")
        if tok in self.variables:
            self._take()
            return ("var", tok)
        raise BooleanParseError(f"unexpected token {tok!r}")


def _evaluate(node, env: dict[str, bool]) -> bool:
    """Iterative post-order evaluation: a long chain of terms must not recurse."""
    stack: list = [(node, False)]
    values: list[bool] = []
    while stack:
        current, expanded = stack.pop()
        kind = current[0]
        if kind == "const":
            values.append(current[1])
        elif kind == "var":
            values.append(env[current[1]])
        elif not expanded:
            stack.append((current, True))
            for child in current[1:]:
                stack.append((child, False))
        elif kind == "not":
            values.append(not values.pop())
        else:
            right, left = values.pop(), values.pop()
            if kind == "and":
                values.append(left and right)
            elif kind == "or":
                values.append(left or right)
            else:
                values.append(left != right)       # xor
    return values[0]


def parse_boolean(expression: str, variables: list[str]):
    """Parse a Boolean expression into a tree. Raises BooleanParseError."""
    # accept "F = A + B" by dropping a left-hand side that is a bare name
    assignment = re.match(r"^\s*[A-Za-z_]\w*\s*=(?!=)\s*(.*)$", expression, re.S)
    if assignment:
        expression = assignment.group(1)
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise BooleanParseError(f"expression longer than {MAX_EXPRESSION_LENGTH} characters")
    return _Parser(_tokenize(expression, variables), variables).parse()


def truth_table(expression: str, variables: list[str]) -> list[int]:
    """Output column for every input row, first variable as the most significant bit."""
    tree = parse_boolean(expression, variables)
    rows = []
    for bits in itertools.product([False, True], repeat=len(variables)):
        rows.append(int(_evaluate(tree, dict(zip(variables, bits, strict=True)))))
    return rows


# ----------------------------------------------------------------------------- truth table check


def _expected_column(spec: dict, variables: list[str]) -> list[int | None]:
    """Expected output per row; None marks a don't-care."""
    n_rows = 2 ** len(variables)
    dont_cares = set(spec.get("dont_cares", []))
    if "expression" in spec:
        column: list[int | None] = list(truth_table(spec["expression"], variables))
    elif "minterms" in spec:
        minterms = set(spec["minterms"])
        column = [1 if i in minterms else 0 for i in range(n_rows)]
    elif "outputs" in spec:
        column = list(spec["outputs"])
        if len(column) != n_rows:
            raise ValueError(f"spec.outputs has {len(column)} rows, expected {n_rows}")
    else:
        raise ValueError("truth_table spec needs one of: expression, minterms, outputs")
    return [None if i in dont_cares else column[i] for i in range(n_rows)]


def extract_expression(text: str, variables: list[str], output_name: str | None = None) -> str:
    """Find the Boolean expression inside a free-text answer.

    Order: the last line that assigns `output_name` ("alarm = ..."), then the whole
    text, then the last line that parses on its own. Raises BooleanParseError if
    nothing in the answer is an expression over the given variables.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if output_name:
        pattern = re.compile(rf"(?:^|\W){re.escape(output_name)}\s*=\s*(.+)$", re.IGNORECASE)
        for line in reversed(lines):
            match = pattern.search(line)
            if match:
                found = _longest_parsable_prefix(match.group(1), variables)
                if found:
                    return found
    candidates = [text.strip(), *reversed(lines)]
    candidates += [line.split("=", 1)[1] for line in reversed(lines) if "=" in line]
    for candidate in candidates:
        found = _longest_parsable_prefix(candidate, variables)
        if found:
            return found
    raise BooleanParseError("no Boolean expression over " + ", ".join(variables) + " was found in the answer")


def _longest_parsable_prefix(text: str, variables: list[str]) -> str | None:
    """'AB + AC + BC because each pair suffices' -> 'AB + AC + BC'. Cuts at word boundaries, longest first."""
    text = text.strip().rstrip(" .;,:")
    cuts = [len(text)] + [m.start() for m in re.finditer(r"\s", text)][::-1]
    for cut in cuts[:80]:
        candidate = text[:cut].rstrip(" .;,:")
        if not candidate:
            continue
        try:
            tree = parse_boolean(candidate, variables)
        except BooleanParseError:
            continue
        if _mentions_variable(tree):
            return candidate
    return None


def _mentions_variable(node) -> bool:
    stack = [node]
    while stack:
        current = stack.pop()
        if current[0] == "var":
            return True
        stack.extend(child for child in current[1:] if isinstance(child, tuple))
    return False


def check_truth_table(spec: dict, answer: dict | str) -> CheckResult:
    """Compare the candidate's expression or table against the expected function.

    spec:   {"variables": ["A","B","C"], "expression" | "minterms" | "outputs": ..., "dont_cares": [..],
             "output_name": "alarm"}
    answer: free text containing an expression, or {"expression": "..."} or {"outputs": [0,1,...]}
    """
    started = time.perf_counter()
    variables: list[str] = spec["variables"]
    expected = _expected_column(spec, variables)

    if isinstance(answer, str):
        answer = {"text": answer}
    try:
        if answer.get("text"):
            got = truth_table(extract_expression(answer["text"], variables, spec.get("output_name")), variables)
        elif answer.get("expression"):
            got = truth_table(answer["expression"], variables)
        elif "outputs" in answer:
            got = [int(bool(v)) for v in answer["outputs"]]
            if len(got) != len(expected):
                raise BooleanParseError(f"table has {len(got)} rows, expected {len(expected)}")
        else:
            raise BooleanParseError("no expression or table in the answer")
    except BooleanParseError as exc:
        return CheckResult(type="truth_table", passed=None, detail=f"could not parse the answer: {exc}",
                           runtime_ms=int((time.perf_counter() - started) * 1000))

    mismatches = []
    for index, (want, have) in enumerate(zip(expected, got, strict=True)):
        if want is not None and want != have:
            bits = format(index, f"0{len(variables)}b")
            mismatches.append({"row": index, "inputs": dict(zip(variables, map(int, bits), strict=True)),
                               "expected": want, "got": have})
    passed = not mismatches
    checked = sum(1 for v in expected if v is not None)
    detail = (f"matches all {checked} specified rows" if passed
              else f"{len(mismatches)} of {checked} specified rows differ")
    return CheckResult(type="truth_table", passed=passed, detail=detail, mismatches=mismatches[:8],
                       runtime_ms=int((time.perf_counter() - started) * 1000))


# ----------------------------------------------------------------------------- numeric check

_SI_PREFIX = {
    "f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "μ": 1e-6, "m": 1e-3,
    "": 1.0, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9, "T": 1e12,
}
_NUMBER_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?")


def _split_unit(unit: str, base_units: set[str]) -> tuple[float, str] | None:
    """Split 'ns' into (1e-9, 's') given the known base units."""
    unit = unit.strip()
    if unit in base_units:
        return 1.0, unit
    for base in sorted(base_units, key=len, reverse=True):
        if unit.endswith(base) and unit[: -len(base)] in _SI_PREFIX:
            return _SI_PREFIX[unit[: -len(base)]], base
    return None


def parse_quantity(text: str | float | int, base_units: set[str]) -> tuple[float, str | None]:
    """Return (value in base units, base unit or None). Raises ValueError if no number is present."""
    if isinstance(text, (int, float)):
        return float(text), None
    match = _NUMBER_RE.search(text)
    if not match:
        raise ValueError("no number found")
    value = float(match.group(0).replace(",", "."))
    rest = text[match.end():].strip().split()
    if rest:
        split = _split_unit(rest[0].strip(".,;"), base_units)
        if split:
            return value * split[0], split[1]
    return value, None


# a named value's clause ends at a sentence end, a connective, or where the next assignment (", fmax = ...") begins
_CLAUSE_END = re.compile(r"[;\n]|\.(?=\s|$)|\s+(?:so|therefore|hence|thus|then|which|giving|and)\s+"
                         r"|,\s*(?=[A-Za-z_][\w ]*?\s*(?:=|:|≈|\bis\b))", re.IGNORECASE)
_QUANTITY_RE = re.compile(rf"({_NUMBER_RE.pattern})\s*([A-Za-zµμΩ]+)?")


def locate_named_value(text: str, names: list[str], *, expected_base: str | None = None,
                       base_units: set[str] | None = None) -> str | None:
    """The value the candidate assigns to a named quantity.

    'Tmin = 1.40 ns, so fmax = 714 MHz' with ['Tmin'] -> '1.40 ns'. With a derivation,
    'Tmin = 0.12 + 1.10 + 0.18 = 1.40 ns', the result is the LAST quantity in that clause that
    carries a compatible unit (here ns), not the first number after the name; without any unit
    in the clause, the last number. The last occurrence of a name wins.
    """
    found = None
    for name in names:
        for match in re.finditer(rf"{re.escape(name)}\s*(?:is|=|:|≈|~|of)?\s*(?:about|approximately|approx\.?)?", text,
                                 re.IGNORECASE):
            clause = text[match.end():]
            stop = _CLAUSE_END.search(clause)
            clause = clause[:stop.start()] if stop else clause
            quantities = [(q.group(1), q.group(2) or "") for q in _QUANTITY_RE.finditer(clause)]
            if not quantities:
                continue
            if expected_base and base_units:
                compatible = [(n, u) for n, u in quantities
                              if u and (split := _split_unit(u.strip(".,;"), base_units)) and split[1] == expected_base]
                if compatible:
                    found = f"{compatible[-1][0]} {compatible[-1][1]}"
                    continue
            number, unit = quantities[-1]
            found = f"{number} {unit}".strip()
    return found


def check_numeric(spec: dict, answer: str | float | int | dict) -> CheckResult:
    """spec: {"expected": 12.5, "unit": "ns", "tolerance_abs": 0.1 | "tolerance_rel": 0.02,
             "output_names": ["Tmin", "minimum period"]}   # optional: which number in a long answer"""
    started = time.perf_counter()
    if isinstance(answer, dict):
        answer = answer.get("value", answer.get("text", ""))
    names = spec.get("output_names") or ([spec["output_name"]] if spec.get("output_name") else [])
    unit = spec.get("unit")
    base_units = {"s", "Hz", "V", "A", "W", "F", "Ω", "ohm", "b", "B", "bit", "bits"}
    expected_factor, expected_base = (1.0, None)
    if unit:
        split = _split_unit(unit, base_units)
        expected_factor, expected_base = split if split else (1.0, unit)
    if names and isinstance(answer, str):
        located = locate_named_value(answer, names, expected_base=expected_base, base_units=base_units)
        if located is None:
            return CheckResult(type="numeric", passed=None,
                               detail=f"no value named {', '.join(names)} was found in the answer",
                               runtime_ms=int((time.perf_counter() - started) * 1000))
        answer = located
    expected = float(spec["expected"]) * expected_factor

    try:
        got, got_base = parse_quantity(answer, base_units)
    except ValueError as exc:
        return CheckResult(type="numeric", passed=None, detail=f"could not read a number: {exc}",
                           runtime_ms=int((time.perf_counter() - started) * 1000))
    if got_base is None:
        got *= expected_factor                     # bare number: assume the unit the question asked for
    elif expected_base and got_base.lower() != expected_base.lower():
        return CheckResult(type="numeric", passed=False,
                           detail=f"unit mismatch: expected {expected_base}, got {got_base}",
                           runtime_ms=int((time.perf_counter() - started) * 1000))

    tolerance = spec.get("tolerance_abs")
    if tolerance is not None:
        tolerance = float(tolerance) * expected_factor
    else:
        tolerance = abs(expected) * float(spec.get("tolerance_rel", 0.01))
    passed = abs(got - expected) <= tolerance + 1e-18
    shown_unit = f" {unit}" if unit else ""
    detail = (f"within tolerance of {spec['expected']}{shown_unit}" if passed
              else f"expected {spec['expected']}{shown_unit}, got {got / expected_factor:g}{shown_unit}")
    return CheckResult(type="numeric", passed=passed, detail=detail,
                       runtime_ms=int((time.perf_counter() - started) * 1000))


# ----------------------------------------------------------------------------- dispatch


# ----------------------------------------------------------------------------- code tests

def check_code_tests(spec: dict, answer: dict | str, *, sandbox: bool = True) -> CheckResult:
    """Run the Python in the answer against the question's cases.

    spec:   {"language": "python", "entry": ["count_set_bits", "popcount"], "timeout_ms": 5000,
             "cases": [{"args": [0], "expected": 0}, {"args": [[6, 6], 12], "accept": [[0, 1]], "unordered": true}]}
    answer: free text; the code is taken from fenced blocks (```python, or untagged blocks that parse).

    passed is None when there is nothing to run (prose, C, pseudocode, or code the audit refused):
    the evaluator still reads the answer. It is False when the code runs and disagrees, raises,
    or never finishes. `sandbox=False` runs in-process and is only for our own seed self-tests.
    """
    started = time.perf_counter()
    cases = spec.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("code_tests spec needs a non-empty 'cases' list")
    if (spec.get("language") or "python") != "python":
        raise ValueError(f"code_tests only runs python, not {spec.get('language')!r}")
    text = answer.get("text", "") if isinstance(answer, dict) else str(answer)

    def done(passed, detail, mismatches=()):
        return CheckResult(type="code_tests", passed=passed, detail=detail, mismatches=list(mismatches)[:8],
                           runtime_ms=int((time.perf_counter() - started) * 1000))

    source = code_runner.extract_python(text)
    if source is None:
        return done(None, "no Python code to run; the answer is reviewed as written")
    refused = code_runner.audit(source)
    if refused:
        return done(None, "the code was not run: " + "; ".join(refused[:3]))
    timeout = max(1.0, float(spec.get("timeout_ms", code_runner.DEFAULT_TIMEOUT_MS)) / 1000)
    outcome = (code_runner.run_in_subprocess(source, spec, timeout_seconds=timeout) if sandbox
               else code_runner.run_cases(source, spec))
    status = outcome.get("status")
    if status == "timeout":
        return done(False, f"the code did not finish within {timeout:g} s (an infinite loop?)")
    if status == "raised":
        return done(False, f"the code raised before any test ran: {outcome.get('error')}")
    if status == "no_entry":
        return done(None, "no function to call was found in the code")
    if status != "ok":
        return done(None, f"the code could not be run here: {outcome.get('error')}")
    results = outcome.get("results", [])
    failed = [r for r in results if not r.get("ok")]
    mismatches = [{"case": r["case"], "inputs": r.get("inputs"), "expected": r.get("expected"),
                   **({"error": r["error"]} if "error" in r else {"got": r.get("got")})} for r in failed]
    entry = outcome.get("entry", "?")
    if not failed:
        return done(True, f"{entry}() passes all {len(results)} test cases", [])
    return done(False, f"{entry}() fails {len(failed)} of {len(results)} test cases", mismatches)


def run_check(deterministic_check: dict | None, answer, *, sandbox: bool = True) -> CheckResult | None:
    """Run the question's deterministic check, if it has one."""
    if not deterministic_check:
        return None
    kind = deterministic_check.get("type")
    spec = deterministic_check.get("spec", {})
    if kind == "truth_table":
        return check_truth_table(spec, answer)
    if kind == "numeric":
        return check_numeric(spec, answer)
    if kind == "code_tests":
        return check_code_tests(spec, answer, sandbox=sandbox)
    if kind == "sim":
        return CheckResult(type="sim", passed=None, detail="simulation checks are not available yet")
    raise ValueError(f"unknown deterministic check type {kind!r}")
