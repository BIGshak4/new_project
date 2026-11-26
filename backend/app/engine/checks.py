"""Deterministic checks (Data_Models §13.4).

A check result is an INPUT to the evaluator, not a replacement for it: a failed
truth table caps correctness, a pass raises the floor, and the rubric still scores
reasoning (AI_Engine_Spec §2.3).

Boolean expressions go through a small parser. Network-submitted Python is never
executed: the former AST filter and child interpreter are not a security sandbox.
Code answers remain available to the evaluator as written. Only explicitly trusted
local seed self-tests may request in-process execution with sandbox=False.
"""

from __future__ import annotations

import asyncio
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


# Every spelling a candidate's keyboard produces is a token here (2026-11-26): a phone turns A' into A’, a textbook
# writes A⋅B and ¬A, a Verilog answer writes s ? a : b. A spelling that is not a token used to end the expression
# early, and the part before it was graded as if it were the whole answer.
_TOKEN_RE = re.compile(
    r"\s*(?:(?P<const>[01])|(?P<ident>[A-Za-z_][A-Za-z_0-9]*)"
    r"|(?P<op>\(|\)|~\^|\^~|~|!|¬|'|’|‘|ʼ|′|´|&&|&|\*|·|⋅|∙|•|×|∧|\|\||\||\+|∨|\^|⊕|⊙|\?|:))"
)

_AND_OPS = {"&", "&&", "*", "·", "⋅", "∙", "•", "×", "∧"}
_OR_OPS = {"|", "||", "+", "∨"}
_XOR_OPS = {"^", "⊕"}
_XNOR_OPS = {"⊙", "~^", "^~"}
_NOT_PREFIX = {"~", "!", "¬"}
_NOT_POSTFIX = {"'", "’", "‘", "ʼ", "′", "´"}
_WORD_OPS = {"and": "&", "or": "|", "xor": "^", "not": "~", "xnor": "⊙", "nand": "nand", "nor": "nor"}


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
    """Precedence: NOT > AND, NAND (explicit or by adjacency) > XOR, XNOR > OR, NOR > the conditional `s ? a : b`."""

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
        node = self._conditional()
        if self._peek() is not None:
            raise BooleanParseError(f"unexpected token {self._peek()!r}")
        return node

    def _conditional(self):
        """`s ? a : b` is (s AND a) OR (NOT s AND b). Each `?` counts as one level of nesting, so a chain is bounded."""
        node = self._or()
        if self._peek() != "?":
            return node
        self._take()
        self.depth += 1
        if self.depth > MAX_NESTING_DEPTH:
            raise BooleanParseError(f"more than {MAX_NESTING_DEPTH} nested parentheses")
        when_true = self._conditional()
        if self._peek() is None:
            raise BooleanParseError("unexpected end of expression")
        if self._peek() != ":":
            raise BooleanParseError(f"unexpected token {self._peek()!r}")
        self._take()
        when_false = self._conditional()
        self.depth -= 1
        return ("or", ("and", node, when_true), ("and", ("not", node), when_false))

    def _or(self):
        node = self._xor()
        while self._peek() in _OR_OPS or self._peek() == "nor":
            negated = self._take() == "nor"
            node = ("or", node, self._xor())
            if negated:
                node = ("not", node)
        return node

    def _xor(self):
        node = self._and()
        while self._peek() in _XOR_OPS or self._peek() in _XNOR_OPS:
            negated = self._take() in _XNOR_OPS
            node = ("xor", node, self._and())
            if negated:
                node = ("not", node)
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
            elif tok == "nand":
                self._take()
                node = ("not", ("and", node, self._not()))
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
        while self._peek() in _NOT_POSTFIX:        # postfix complement: A', and the apostrophes a phone types for it
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
            node = self._conditional()
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
    text = _collapse_whitespace(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if output_name:
        pattern = re.compile(rf"(?:^|\W){re.escape(output_name)}\s*=\s*(.+)$", re.IGNORECASE)
        for line in reversed(lines):
            match = pattern.search(line)
            if match:
                found = _stated_expression(_first_statement(match.group(1), variables), variables)
                if found:
                    return found
    candidates = list(reversed(lines))
    candidates += [line.split("=", 1)[1] for line in reversed(lines) if "=" in line]
    candidates += [line.rsplit(":", 1)[1] for line in reversed(lines) if ":" in line]   # "A majority vote: AB + BC + AC"
    # something that is an expression from end to end is believed before anything cut out of a longer text
    for candidate in [text.strip(), *candidates]:
        whole = candidate.strip().rstrip(" .;,:")
        if _reads_as_expression(whole, variables):
            return whole
    for candidate in [*candidates, text.strip()]:
        found = _longest_parsable_prefix(candidate, variables)
        if found:
            return found
    raise BooleanParseError("no Boolean expression over " + ", ".join(variables) + " was found in the answer")


# What may follow the expression is prose: words, digits and the punctuation of a sentence. If the text that would be
# cut off holds anything else (an operator, a symbol the parser does not read, a combining overline) or an operator
# written as a word it does not know, it is the rest of the expression, and grading the part before it marked right
# answers wrong ("A ⋅ B + A ⋅ C'" graded as "A") and a wrong one right (bug hunt, 2026-11-26). Then nothing is
# graded: the check says it could not read the answer, and the judge decides without it.
_EXPRESSION_MARK = re.compile(r"[^\w\s.,;:!?()\[\]\"'’‘“”\-–—/%]|_"
                              r"|\b(?:implies|iff|equals|nxor|exor|eor|plus|minus|times)\b", re.IGNORECASE)
_NEXT_ASSIGNMENT = re.compile(r"(?:;|,|\s)\s*([A-Za-z_]\w*)\s*=(?!=)")


def _first_statement(text: str, variables: list[str]) -> str:
    """'E&A1&~A0; Y3 = E&A1&A0' -> 'E&A1&~A0': where another output is assigned, this one's expression is over.
    A name made of the question's variables is not another output ('A + B = B + A' stays whole)."""
    known = set(variables)
    single_letter = all(len(v) == 1 for v in variables)
    for match in _NEXT_ASSIGNMENT.finditer(text):
        name = match.group(1)
        if name in known or name.lower() in _WORD_OPS or (single_letter and all(ch in known for ch in name)):
            continue
        return text[:match.start()]
    return text.split(";", 1)[0]


def _reads_as_expression(text: str, variables: list[str]) -> bool:
    try:
        return _mentions_variable(parse_boolean(text.strip(), variables))
    except BooleanParseError:
        return False


def _stated_expression(statement: str, variables: list[str]) -> str | None:
    """"(A+B)' = A'B'" -> "A'B'": in a chain of equal forms the last one is the answer. Anything else after an equals
    sign ('AB + AC = alarm when two agree') is not a form, and the part before it is read."""
    parts = statement.split("=")
    if len(parts) > 1 and all(_reads_as_expression(part, variables) for part in parts[:-1]):
        found = _longest_parsable_prefix(parts[-1], variables)
        if found:
            return found
    return _longest_parsable_prefix(parts[0] if len(parts) > 1 else statement, variables)


def _longest_parsable_prefix(text: str, variables: list[str]) -> str | None:
    """'AB + AC + BC because each pair suffices' -> 'AB + AC + BC'. Cuts at word boundaries, longest first."""
    text = _first_statement(text, variables).strip().rstrip(" .;,:")
    cuts = [len(text)] + [m.start() for m in re.finditer(r"\s", text)][::-1]
    for cut in cuts[:80]:
        if _EXPRESSION_MARK.search(text, cut):
            return None                            # every shorter cut leaves this operator behind too
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


# The answer editor puts a named table first and keeps the learner's prose and code after it.
_WRITTEN_TABLE = re.compile(r"^~~~truth-table\n(.*?)\n~~~(?:\n|$)", re.DOTALL)


def _submitted_table_column(body: str, variables: list[str], output_name: str | None) -> list[int | str]:
    lines = body.split("\n")
    if len(lines) < 3 or not lines[0].startswith("inputs\t") or not lines[1].startswith("outputs\t"):
        raise BooleanParseError("invalid truth table headers")
    inputs = [name.strip().casefold() for name in lines[0].split("\t")[1:]]
    outputs = [name.strip().casefold() for name in lines[1].split("\t")[1:]]
    expected_inputs = [name.casefold() for name in variables]
    if len(inputs) > 6 or sorted(inputs) != sorted(expected_inputs):
        raise BooleanParseError("the input columns must match " + ", ".join(variables))
    if not 1 <= len(outputs) <= 8 or len(lines) - 2 != 2 ** len(inputs):
        raise BooleanParseError("unexpected number of rows or outputs")
    if len(outputs) == 1:
        output_index = 0
    elif output_name and outputs.count(output_name.casefold()) == 1:
        output_index = outputs.index(output_name.casefold())
    else:
        raise BooleanParseError("the expected output column could not be identified")

    # Input columns may appear in a different order from the question's variables.
    positions = [inputs.index(name) for name in expected_inputs]
    result: list[int | str] = ["-"] * (len(lines) - 2)
    for row, line in enumerate(lines[2:]):
        bits, *cells = line.split("\t")
        if (
            bits != format(row, f"0{len(inputs)}b")
            or len(cells) != len(outputs)
            or any(cell not in {"0", "1", "X", "-"} for cell in cells)
        ):
            raise BooleanParseError("invalid truth table row")
        index = int("".join(bits[pos] for pos in positions), 2)
        cell = cells[output_index]
        result[index] = int(cell) if cell in {"0", "1"} else cell
    return result


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
            text = answer["text"]
            table = _WRITTEN_TABLE.match(text)
            if table:
                got = _submitted_table_column(table[1], variables, spec.get("output_name"))
                if any(want is not None and have == "-" for want, have in zip(expected, got, strict=True)):
                    raise BooleanParseError("some required output cells are empty")
            else:
                got = truth_table(extract_expression(text, variables, spec.get("output_name")), variables)
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
# 1,493,000 (digit groups) | 1.4 or 1,4 | .6 ; each with an optional exponent
_NUMBER_RE = re.compile(r"[-+]?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:[.,]\d+)?|\.\d+)(?:[eE][-+]?\d+)?")
_GROUPED_NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?")

# units written as words: "1400 picoseconds", "1.4e-9 seconds", "1400 psec"
_UNIT_WORDS = {"second": "s", "seconds": "s", "sec": "s", "secs": "s", "hertz": "Hz", "volt": "V", "volts": "V",
               "amp": "A", "amps": "A", "ampere": "A", "amperes": "A", "watt": "W", "watts": "W",
               "farad": "F", "farads": "F", "ohm": "Ω", "ohms": "Ω", "bit": "bit", "bits": "bit"}
_PREFIX_WORDS = {"femto": "f", "pico": "p", "nano": "n", "micro": "u", "milli": "m", "kilo": "k", "mega": "M",
                 "giga": "G", "tera": "T"}
_SAME_BASE = {"ohm": "Ω", "ohms": "Ω", "bits": "bit"}                 # one unit, several spellings

_UNICODE_MINUS = str.maketrans({"−": "-", "﹣": "-", "－": "-"})
_TIMES_TEN = re.compile(r"(?<=\d) ?[x×*·⋅] ?10 ?\^ ?\(? ?([-+]?\d+) ?\)?")    # 1.4 x 10^-9
_BARE_TEN = re.compile(r"(?<![\w.,])10 ?\^ ?\(? ?([-+]?\d+) ?\)?")           # 10^8


def _same_base(one: str | None, other: str | None) -> bool:
    if one is None or other is None:
        return one is other
    return _SAME_BASE.get(one, one).lower() == _SAME_BASE.get(other, other).lower()


def _split_unit(unit: str, base_units: set[str]) -> tuple[float, str] | None:
    """Split 'ns' into (1e-9, 's') given the known base units; 'picoseconds' and 'psec' too."""
    unit = unit.strip()
    if unit in base_units:
        return 1.0, unit
    for base in sorted(base_units, key=len, reverse=True):
        if unit.endswith(base) and unit[: -len(base)] in _SI_PREFIX:
            return _SI_PREFIX[unit[: -len(base)]], base
    word, factor = unit.lower(), 1.0
    for prefix_word, letter in _PREFIX_WORDS.items():
        if word.startswith(prefix_word) and word[len(prefix_word):] in _UNIT_WORDS:
            word, factor = word[len(prefix_word):], _SI_PREFIX[letter]
            break
    else:
        if word[:1] in ("f", "p", "n", "u", "µ", "μ", "m") and word[1:] in ("sec", "secs"):
            word, factor = word[1:], _SI_PREFIX[word[0]]
    base = _UNIT_WORDS.get(word)
    if base is None:
        return None
    for known in base_units:
        if _same_base(known, base):
            return factor, known
    return None


def _normalize_numbers(text: str) -> str:
    """One spelling for what a number can look like: a typographic minus, and powers of ten written out."""
    text = _collapse_whitespace(text).translate(_UNICODE_MINUS)
    text = _TIMES_TEN.sub(lambda m: "e" + m.group(1), text)
    return _BARE_TEN.sub(lambda m: "1e" + m.group(1), text)


def _number_readings(token: str) -> list[float]:
    """What the written number can mean. '1,493' is 1.493 with a decimal comma and 1493 with a digit group, and the
    text alone does not say which: both are returned, and the answer is right if either is."""
    sign = -1.0 if token.startswith("-") else 1.0
    mantissa, _, exponent = token.lstrip("+-").lower().partition("e")
    scale = 10.0 ** int(exponent) if exponent else 1.0
    if _GROUPED_NUMBER.fullmatch(mantissa):
        grouped = sign * float(mantissa.replace(",", "")) * scale
        if mantissa.count(",") == 1 and "." not in mantissa:
            return [sign * float(mantissa.replace(",", ".")) * scale, grouped]
        return [grouped]
    return [sign * float(mantissa.replace(",", ".")) * scale]


def _quantity_readings(text: str | float | int, base_units: set[str]) -> tuple[list[float], str | None]:
    if isinstance(text, (int, float)):
        return [float(text)], None
    match = _NUMBER_RE.search(text)
    if not match:
        raise ValueError("no number found")
    values = _number_readings(match.group(0))
    rest = text[match.end():].strip().split()
    if rest:
        split = _split_unit(rest[0].strip(".,;)"), base_units)
        if split:
            return [value * split[0] for value in values], split[1]
    return values, None


def parse_quantity(text: str | float | int, base_units: set[str]) -> tuple[float, str | None]:
    """Return (value in base units, base unit or None). Raises ValueError if no number is present."""
    values, base = _quantity_readings(text, base_units)
    return values[0], base


# a named value's clause ends at a sentence end, a connective, or where the next assignment (", fmax = ...") begins
_CLAUSE_END = re.compile(r"[;\n]|\.(?=\s|$)|\s+(?:so|therefore|hence|thus|then|which|giving|and)\s+"
                         r"|,\s*(?=[A-Za-z_][\w ]*?\s*(?:=|:|≈|\bis\b))", re.IGNORECASE)
_QUANTITY_RE = re.compile(rf"({_NUMBER_RE.pattern})\s*([A-Za-zµμΩ]+)?")
_WHITESPACE_RUN = re.compile(r"\s{2,}")
_NAME_LINK = r"\s*(?P<link>is|=|:|≈|~|of)?\s*(?:about|approximately|approx\.?)?"
_BRACKETED = re.compile(r"\([^()]*\)")
_OTHER_BASE_LITERAL = re.compile(r"(?<![\w.])(?:0[xX][0-9A-Fa-f]+|0[bB][01]+)\b")
_NEW_ASSIGNMENT = re.compile(r"(?<![\w.])[A-Za-z_]\w*\s*(?:=|≈)")
_EQUALS = re.compile(r"=|≈")
_ARITHMETIC = {"+", "-", "*", "/", "×", "·", "⋅", "x", "X"}
# The work per answer is bounded: a name's clause is read inside this window, and only a name's last occurrences are
# read. Before, every occurrence rescanned the rest of the answer, so "Tmin=1 " repeated to the 20,000-character cap
# cost about a minute of processor time before any model call (bug hunt, 2026-11-26; SEC-016 was the blank-run case).
CLAUSE_WINDOW = 400
OCCURRENCES_READ = 40


def _collapse_whitespace(text: str) -> str:
    """One space, or one newline when the run had one. `_CLAUSE_END`'s connective alternation (blanks, a word, blanks) is quadratic over
    a long run of blanks (8,000 spaces: 2.6 s per scan, repeated per name), so a padded answer could pin a CPU for a
    minute before any model call (security review SEC-016, 2026-11-08). Collapsing the runs first is linear."""
    return _WHITESPACE_RUN.sub(lambda m: "\n" if "\n" in m.group() else " ", text)


def _written(quantity: re.Match) -> str:
    return f"{quantity.group(1)} {quantity.group(2) or ''}".strip()


def _stated_value(clause: str, expected_base: str | None, base_units: set[str] | None) -> tuple[str | None, list[str]]:
    """(the value this clause states for its name, every quantity written in the clause).

    The stated value is None when the clause does not say which number it is. How a clause is read:
    'Tmin = 0.12 + 1.10 + 0.18 = 1.40 ns' states 1.40 ns (what follows the last equals sign);
    'Tmin = 1.40 ns (tcq 0.12 ns + ...)' states 1.40 ns (brackets are an aside);
    'c = 107 because a = 5' states 107 (a new assignment ends the clause);
    'acc = -31 (0x21)' states -31 (a hexadecimal or binary literal is not a second value);
    'Tmin = 0.12 + 1.10 + 0.18 ns' states nothing (a sum the candidate did not work out).
    """
    clause = _OTHER_BASE_LITERAL.sub(" ", clause)
    mentioned = [_written(q) for q in _QUANTITY_RE.finditer(clause)]
    core = clause
    for _ in range(4):                                             # nested brackets, innermost first
        without = _BRACKETED.sub(" ", core)
        if without == core:
            break
        core = without
    core = core.split("(", 1)[0]                                   # a bracket the clause end cut open
    if not _QUANTITY_RE.search(core):
        core = clause                                              # 'Tmin = (1.4 ns)': the value was the bracket
    for start in _NEW_ASSIGNMENT.finditer(core):
        before = core[:start.start()].rstrip()
        # 'tcq + tsetup = 1.4' continues the sum, and '33 unsigned = -31 signed' annotates a number
        if before and before[-1] not in "+-*/×·⋅(=≈" and not before[-1].isdigit():
            core = before
            break
    found: list[re.Match] = []
    segment = ""
    for segment in reversed(_EQUALS.split(core)):                  # 'c = 107 = a + b': the last part that has a number
        found = list(_QUANTITY_RE.finditer(segment))
        if found:
            break
    if not found:
        return None, mentioned
    index = 0
    if expected_base and base_units:
        for position, quantity in enumerate(found):
            split = _split_unit((quantity.group(2) or "").strip(".,;"), base_units) if quantity.group(2) else None
            if split and _same_base(split[1], expected_base):
                index = position
                break

    def summed(left: re.Match, right: re.Match) -> bool:
        between = segment[left.end():right.start()].strip(" ()")
        return between in _ARITHMETIC or (not between and right.group(1)[0] in "+-")

    if (index + 1 < len(found) and summed(found[index], found[index + 1])) or (index and summed(found[index - 1], found[index])):
        return None, mentioned
    return _written(found[index]), mentioned


def _named_readings(text: str, names: list[str], expected_base: str | None,
                    base_units: set[str] | None) -> tuple[str | None, list[str]] | None:
    """What the answer says about the named quantity: (its stated value or None, every quantity near the name).
    None when no name is followed by a number.

    A name is a whole word ('c' is not found in 'because', 'acc' not in 'accumulator'). An occurrence that links the
    name to its value ('N = 4', 'Tmin is 1.4 ns') is believed over one that merely stands next to a number
    ('3 stages give an MTBF of 2 years'); among equals a later name of the list, then the later occurrence, wins.
    """
    text = _collapse_whitespace(text)
    best: tuple[tuple[bool, int, int], str | None] | None = None
    mentioned: list[str] = []
    for order, name in enumerate(names):
        pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_]){_NAME_LINK}", re.IGNORECASE)
        for match in list(pattern.finditer(text))[-OCCURRENCES_READ:]:
            clause = text[match.end():match.end() + CLAUSE_WINDOW]
            stop = _CLAUSE_END.search(clause)
            stated, quantities = _stated_value(clause[:stop.start()] if stop else clause, expected_base, base_units)
            if not quantities:
                continue
            mentioned += quantities
            rank = (bool(match.group("link")), order, match.start())
            if best is None or rank > best[0]:
                best = (rank, stated)
    return None if best is None else (best[1], mentioned)


def locate_named_value(text: str, names: list[str], *, expected_base: str | None = None,
                       base_units: set[str] | None = None) -> str | None:
    """The value the candidate assigns to a named quantity, or None when the answer does not state one.

    'Tmin = 1.40 ns, so fmax = 714 MHz' with ['Tmin'] -> '1.40 ns'. See `_stated_value` for how a clause is read.
    """
    read = _named_readings(text, names, expected_base, base_units)
    return read[0] if read else None


NOT_ONE_VALUE = "more than one value could be the answer for {names}; it was not checked automatically"


def check_numeric(spec: dict, answer: str | float | int | dict) -> CheckResult:
    """spec: {"expected": 12.5, "unit": "ns", "tolerance_abs": 0.1 | "tolerance_rel": 0.02,
             "output_names": ["Tmin", "minimum period"]}   # optional: which number in a long answer

    With `output_names` the check gives a verdict only when the answer is plain about it: passed when the value the
    answer states for the name is the expected one, failed when no number near the name is, and None (the judge
    decides without the check) when the stated value is wrong but the expected one stands next to it, or when the
    answer leaves a sum unfinished. A wrong verdict here caps or lifts the judge's score, so doubt is not a verdict."""
    started = time.perf_counter()

    def result(passed: bool | None, detail: str) -> CheckResult:
        return CheckResult(type="numeric", passed=passed, detail=detail, runtime_ms=int((time.perf_counter() - started) * 1000))

    if isinstance(answer, dict):
        answer = answer.get("value", answer.get("text", ""))
    if isinstance(answer, str):
        # Numeric questions grade the written result, never bits from an attached table.
        answer = _normalize_numbers(_WRITTEN_TABLE.sub("", answer, count=1))
    names = spec.get("output_names") or ([spec["output_name"]] if spec.get("output_name") else [])
    unit = spec.get("unit")
    base_units = {"s", "Hz", "V", "A", "W", "F", "Ω", "ohm", "b", "B", "bit", "bits"}
    expected_factor, expected_base = (1.0, None)
    if unit:
        split = _split_unit(unit, base_units)
        expected_factor, expected_base = split if split else (1.0, unit)
    expected = float(spec["expected"]) * expected_factor
    tolerance = spec.get("tolerance_abs")
    if tolerance is not None:
        tolerance = float(tolerance) * expected_factor
    else:
        tolerance = abs(expected) * float(spec.get("tolerance_rel", 0.01))
    slack = 1e-9 * max(abs(expected), abs(tolerance)) + 1e-18      # 3.4 - 3.3 is 0.10000000000000009 in floating point

    def agrees(written: str | float | int) -> bool | None:
        """True or False when the unit fits; None when it is another kind of unit."""
        values, base = _quantity_readings(written, base_units)
        if base is None:
            values = [value * expected_factor for value in values]    # bare number: assume the unit the question asked for
        elif expected_base and not _same_base(base, expected_base):
            return None
        return any(abs(value - expected) <= tolerance + slack for value in values)

    others: list[str] = []
    if names and isinstance(answer, str):
        read = _named_readings(answer, names, expected_base, base_units)
        if read is None:
            return result(None, f"no value named {', '.join(names)} was found in the answer")
        stated, others = read
        if stated is None:
            return result(None, NOT_ONE_VALUE.format(names=", ".join(names)))
        answer = stated

    try:
        got_values, got_base = _quantity_readings(answer, base_units)
        passed = agrees(answer)
    except ValueError as exc:
        return result(None, f"could not read a number: {exc}")
    if not passed and any(agrees(other) for other in others):
        return result(None, NOT_ONE_VALUE.format(names=", ".join(names)))
    if passed is None:
        return result(False, f"unit mismatch: expected {expected_base}, got {got_base}")
    shown_unit = f" {unit}" if unit else ""
    got = got_values[0] * (expected_factor if got_base is None else 1.0)
    return result(passed, f"within tolerance of {spec['expected']}{shown_unit}" if passed
                  else f"expected {spec['expected']}{shown_unit}, got {got / expected_factor:g}{shown_unit}")


# ----------------------------------------------------------------------------- dispatch


# ----------------------------------------------------------------------------- code tests

CODE_EXECUTION_UNAVAILABLE = "Automatic code execution is unavailable; the answer is reviewed as written."


def _code_execution_unavailable() -> CheckResult:
    return CheckResult(type="code_tests", passed=None, detail=CODE_EXECUTION_UNAVAILABLE, runtime_ms=0)


def check_code_tests(spec: dict, answer: dict | str, *, sandbox: bool = True) -> CheckResult:
    """Reject untrusted execution, or check an explicitly trusted local seed.

    spec:   {"language": "python", "entry": ["count_set_bits", "popcount"], "timeout_ms": 5000,
             "cases": [{"args": [0], "expected": 0}, {"args": [[6, 6], 12], "accept": [[0, 1]], "unordered": true}]}
    answer: free text; the code is taken from fenced blocks (```python, or untagged blocks that parse).

    The legacy sandbox=True default FAILS CLOSED before extraction, parsing or
    execution. No environment variable enables it. A child Python interpreter
    with an AST filter does not isolate filesystem, process or network access.
    sandbox=False executes in-process and is exclusively for developer-reviewed
    seed self-tests, never HTTP input or unreviewed model-generated code.
    """
    if sandbox:
        return _code_execution_unavailable()
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
    outcome = code_runner.run_cases(source, spec)
    status = outcome.get("status")
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


async def run_check_async(deterministic_check: dict | None, answer) -> CheckResult | None:
    """The HTTP-facing check boundary: never execute submitted source code.

    Truth-table and numeric checks keep their existing bounded parser behavior.
    """
    if not deterministic_check:
        return None
    if deterministic_check.get("type") == "code_tests":
        return _code_execution_unavailable()
    return await asyncio.to_thread(run_check, deterministic_check, answer)


def run_check(deterministic_check: dict | None, answer, *, sandbox: bool = True) -> CheckResult | None:
    """Run a bounded check; source execution is disabled by default.

    sandbox=False is a trusted-local-seed escape hatch, not a runtime feature flag.
    Network handlers must use run_check_async, which offers no such option.
    """
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
