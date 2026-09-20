"""A drawn circuit as text: a netlist the evaluator can read and Boolean functions the checks can test.

The frontend stores a bounded, validated `Circuit` (parts + wires, see schemas/visual_answer.py and
apps/web/src/lib/circuit.ts). Nothing here simulates timing; for one-bit combinational logic the
output functions are derived symbolically (`alarm = (A & B) | (B & C)`), which is exactly the form
`checks.extract_expression` reads, so a drawn majority gate passes the same truth-table check as a
typed one. Sequential parts, buses and selectors wider than 2:1 are described but not derived.
"""

from __future__ import annotations

from app.schemas.visual_answer import Circuit, CircuitPart

_GATE_OPS = {"and": "&", "nand": "&", "or": "|", "nor": "|", "xor": "^", "xnor": "^"}
_INVERTING = {"nand", "nor", "xnor", "not"}
_SOURCES = {"input", "constant", "clock"}


def ports(part: CircuitPart) -> tuple[list[str], list[str]]:
    """(inputs, outputs) port ids, mirroring circuit.ts `ports()`."""
    kind, n, bits = part.kind, part.count, part.bits
    if kind in ("input", "constant", "clock"):
        return [], ["Q"]
    if kind == "output":
        return ["D"], []
    if kind in ("not", "buffer"):
        return ["A"], ["Y"]
    if kind == "mux":
        return [f"D{i}" for i in range(n)] + ["S"], ["Y"]
    if kind == "demux":
        return ["D", "S"], [f"Y{i}" for i in range(n)]
    if kind == "encoder":
        return [f"D{i}" for i in range(n)], ["Y", "V"]
    if kind == "decoder":
        return ["A"], [f"Y{i}" for i in range(n)]
    if kind == "half-adder":
        return ["A", "B"], ["S", "C"]
    if kind in ("full-adder", "adder"):
        return ["A", "B", "Cin"], ["S", "Cout"]
    if kind == "comparator":
        return ["A", "B"], ["GT", "EQ", "LT"]
    if kind in ("dff", "register"):
        return ["D", "CLK", "RST"], ["Q", "QN"]
    if kind == "counter":
        return ["EN", "CLK", "RST"], ["Q"]
    if kind == "splitter":
        return ["D"], [f"B{i}" for i in range(bits)]
    if kind == "joiner":
        return [f"B{i}" for i in range(bits)], ["Y"]
    return [f"A{i}" for i in range(n)], ["Y"]


def _name(part: CircuitPart) -> str:
    label = " ".join(part.label.split())
    return label or part.kind.upper()


class _Deriver:
    def __init__(self, circuit: Circuit):
        self.parts = {p.id: p for p in circuit.parts}
        self.driver = {(w.target, w.targetPort): (w.source, w.sourcePort) for w in circuit.wires}
        self.memo: dict[tuple[str, str], str | None] = {}
        self.active: set[tuple[str, str]] = set()

    def signal(self, part_id: str, port: str) -> str | None:
        """The Boolean expression driving (part, output port), or None when it is not one-bit combinational."""
        key = (part_id, port)
        if key in self.memo:
            return self.memo[key]
        if key in self.active:                     # feedback loop: not combinational
            return None
        self.active.add(key)
        try:
            value = self._compute(self.parts[part_id], port)
        finally:
            self.active.discard(key)
        self.memo[key] = value
        return value

    def incoming(self, part_id: str, port: str) -> str | None:
        source = self.driver.get((part_id, port))
        return self.signal(*source) if source else None

    def _compute(self, part: CircuitPart, port: str) -> str | None:
        kind = part.kind
        if part.bits != 1 and kind not in ("output",):
            return None
        if kind == "input":
            return _identifier(_name(part))
        if kind == "constant":
            return "1" if part.value & 1 else "0"
        if kind == "clock":
            return None
        if kind in _GATE_OPS:
            inputs = [self.incoming(part.id, f"A{i}") for i in range(part.count)]
            if any(i is None for i in inputs):
                return None
            joined = f" {_GATE_OPS[kind]} ".join(inputs)
            return f"~({joined})" if kind in _INVERTING else f"({joined})"
        if kind in ("not", "buffer"):
            a = self.incoming(part.id, "A")
            if a is None:
                return None
            return f"~{_atom(a)}" if kind == "not" else a
        if kind == "mux" and part.count == 2:
            d0, d1, s = (self.incoming(part.id, p) for p in ("D0", "D1", "S"))
            if None in (d0, d1, s):
                return None
            return f"((~{_atom(s)} & {d0}) | ({s} & {d1}))"
        if kind == "half-adder" and port in ("S", "C"):
            a, b = self.incoming(part.id, "A"), self.incoming(part.id, "B")
            if a is None or b is None:
                return None
            return f"({a} ^ {b})" if port == "S" else f"({a} & {b})"
        if kind == "full-adder" and port in ("S", "Cout"):
            a, b, c = (self.incoming(part.id, p) for p in ("A", "B", "Cin"))
            if a is None or b is None:
                return None
            c = c or "0"
            if port == "S":
                return f"({a} ^ {b} ^ {c})"
            return f"(({a} & {b}) | ({c} & ({a} ^ {b})))"
        return None


def _identifier(label: str) -> str:
    return label.replace(" ", "_")


def _atom(expr: str) -> str:
    return expr if expr.startswith("(") or expr.startswith("~") or expr.isalnum() or "_" in expr else f"({expr})"


def boolean_functions(circuit: Circuit) -> dict[str, str | None]:
    """{output label: expression or None} for every OUTPUT pin in the drawing."""
    deriver = _Deriver(circuit)
    functions: dict[str, str | None] = {}
    for part in circuit.parts:
        if part.kind == "output":
            functions[_name(part)] = deriver.incoming(part.id, "D") if part.bits == 1 else None
    return functions


def check_lines(circuit: Circuit) -> str:
    """`label = expression` lines the deterministic checks read, one per derived output."""
    return "\n".join(f"{_identifier(label)} = {expr}" for label, expr in boolean_functions(circuit).items() if expr)


def describe(circuit: Circuit) -> str:
    """The netlist in plain text for the evaluator: components, connections, derived functions, loose ends."""
    parts = {p.id: p for p in circuit.parts}
    lines = [f"Components ({len(circuit.parts)}):"]
    for p in circuit.parts:
        extra = []
        if p.kind in _GATE_OPS or p.kind in ("mux", "demux", "encoder", "decoder"):
            extra.append(f"{p.count} inputs" if p.kind in _GATE_OPS else f"{p.count}-way")
        if p.bits != 1:
            extra.append(f"{p.bits}-bit")
        if p.kind == "constant":
            extra.append(f"value {p.value}")
        lines.append(f"- {p.kind.upper()} \"{_name(p)}\"" + (f" ({', '.join(extra)})" if extra else ""))
    lines.append(f"Wires ({len(circuit.wires)}):")
    for w in circuit.wires:
        src, dst = parts.get(w.source), parts.get(w.target)
        if src and dst:
            lines.append(f"- {_name(src)}.{w.sourcePort} -> {_name(dst)}.{w.targetPort}")
    driven = {(w.target, w.targetPort) for w in circuit.wires}
    loose = []
    for p in circuit.parts:
        inputs, _ = ports(p)
        for port in inputs:
            if (p.id, port) not in driven and port not in ("RST", "Cin"):
                loose.append(f"{_name(p)}.{port}")
    if loose:
        lines.append("Unconnected inputs: " + ", ".join(loose[:12]) + (" ..." if len(loose) > 12 else ""))
    functions = boolean_functions(circuit)
    if functions:
        lines.append("Derived Boolean functions (one-bit combinational logic only):")
        for label, expr in functions.items():
            lines.append(f"  {label} = {expr}" if expr else f"  {label}: not derived (sequential, bus or undriven)")
    else:
        lines.append("No OUTPUT pin is placed, so no function can be derived.")
    return "\n".join(lines)
