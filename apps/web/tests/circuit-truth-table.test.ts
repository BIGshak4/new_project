import test from "node:test";
import assert from "node:assert/strict";
import {
  truthTable,
  truthTablePlan,
  type Circuit,
  type Kind,
  type Part,
  type TruthTable,
} from "../src/lib/circuit";

const part = (id: string, kind: Kind, patch: Partial<Part> = {}): Part => ({
  id, kind, label: id, bits: 1, count: 2, value: 0, x: 0, y: 0, ...patch,
});
const wire = (source: string, sourcePort: string, target: string, targetPort: string) => ({
  id: `${source}.${sourcePort}-${target}.${targetPort}`, source, sourcePort, target, targetPort,
});
function binary(kind: Kind): Circuit {
  return {
    version: 1,
    parts: [part("A", "input", { value: 1 }), part("B", "input"), part("gate", kind), part("Y", "output")],
    wires: [wire("A", "Q", "gate", "A0"), wire("B", "Q", "gate", "A1"), wire("gate", "Y", "Y", "D")],
  };
}
function generated(c: Circuit): TruthTable {
  const result = truthTable(c);
  if (!result.ok) assert.fail(result.issue);
  return result;
}

test("AND and XOR enumerate the same inputs in ascending binary order", () => {
  const expected = [[0, 0], [0, 1], [1, 0], [1, 1]];
  for (const [kind, values] of [["and", [0, 0, 0, 1]], ["xor", [0, 1, 1, 0]]] as const) {
    const table = generated(binary(kind));
    assert.deepEqual(table.rows.map((r) => r.inputs), expected);
    assert.deepEqual(table.rows.map((r) => r.outputs[0]), values);
    assert.equal(table.hasUnknown, false);
    assert.deepEqual(table.inputs.map((p) => p.label), ["A", "B"]);
  }
});

test("enumeration preserves frozen source objects and current input/constant values", () => {
  const c = binary("xor");
  c.parts[1].kind = "constant";
  c.parts[1].value = 1;
  const original = JSON.stringify(c);
  for (const p of c.parts) Object.freeze(p);
  for (const w of c.wires) Object.freeze(w);
  Object.freeze(c.parts);
  Object.freeze(c.wires);
  Object.freeze(c);
  const table = generated(c);
  assert.deepEqual(table.rows, [
    { inputs: [0], outputs: [1] },
    { inputs: [1], outputs: [0] },
  ]);
  assert.equal(JSON.stringify(c), original);
});

test("constants-only circuits produce one row rather than inventing input variables", () => {
  const c: Circuit = {
    version: 1,
    parts: [part("fixed", "constant", { bits: 3, value: 5 }), part("Y", "output", { bits: 3 })],
    wires: [wire("fixed", "Q", "Y", "D")],
  };
  const table = generated(c);
  assert.deepEqual(table.inputs, []);
  assert.deepEqual(table.rows, [{ inputs: [], outputs: [5] }]);
});

test("multi-bit INPUT components enumerate their bus values and count all variable bits", () => {
  const c: Circuit = {
    version: 1,
    parts: [part("A", "input", { bits: 2 }), part("B", "input"), part("Y", "output", { bits: 2 })],
    wires: [wire("A", "Q", "Y", "D")],
  };
  const table = generated(c);
  assert.equal(table.inputBits, 3);
  assert.deepEqual(table.rows.map((r) => r.inputs), [[0, 0], [0, 1], [1, 0], [1, 1], [2, 0], [2, 1], [3, 0], [3, 1]]);
  assert.deepEqual(table.rows.map((r) => r.outputs[0]), [0, 0, 1, 1, 2, 2, 3, 3]);
});

test("six variable bits produce at most 64 rows; seven are blocked before simulation", () => {
  const c: Circuit = {
    version: 1,
    parts: [part("A", "input", { bits: 6 }), part("Y", "output", { bits: 6 })],
    wires: [wire("A", "Q", "Y", "D")],
  };
  assert.equal(generated(c).rows.length, 64);
  assert.deepEqual(generated(c).rows.at(-1), { inputs: [63], outputs: [63] });
  c.parts[0].bits = 7;
  c.parts[1].bits = 7;
  assert.deepEqual(truthTable(c), { ok: false, issue: "too-many-inputs", inputBits: 7 });
});

test("six separate one-bit inputs include every AND combination exactly once", () => {
  const c: Circuit = {
    version: 1,
    parts: [...Array.from({ length: 6 }, (_, i) => part(`A${i}`, "input")), part("g", "and", { count: 6 }), part("Y", "output")],
    wires: [...Array.from({ length: 6 }, (_, i) => wire(`A${i}`, "Q", "g", `A${i}`)), wire("g", "Y", "Y", "D")],
  };
  const table = generated(c);
  assert.equal(table.rows.length, 64);
  assert.equal(new Set(table.rows.map((r) => r.inputs.join(""))).size, 64);
  assert.deepEqual(table.rows.flatMap((r) => r.outputs), [...Array(63).fill(0), 1]);
});

test("every explicit OUTPUT is included, including a full adder's separate sum and carry", () => {
  const c: Circuit = {
    version: 1,
    parts: [part("A", "input"), part("B", "input"), part("Cin", "input"), part("g", "full-adder"), part("S", "output"), part("Cout", "output")],
    wires: [wire("A", "Q", "g", "A"), wire("B", "Q", "g", "B"), wire("Cin", "Q", "g", "Cin"), wire("g", "S", "S", "D"), wire("g", "Cout", "Cout", "D")],
  };
  const table = generated(c);
  for (const row of table.rows) {
    const sum = row.inputs.reduce((a, b) => a + b, 0);
    assert.deepEqual(row.outputs, [sum & 1, sum >> 1]);
  }
});

test("empty circuits and drawings without OUTPUT probes explain how to proceed", () => {
  assert.deepEqual(truthTablePlan({ version: 1, parts: [], wires: [] }), { ok: false, issue: "empty", inputBits: 0 });
  const c = binary("and");
  c.parts.pop();
  c.wires.pop();
  assert.deepEqual(truthTable(c), { ok: false, issue: "no-output", inputBits: 2 });
});

test("an undriven OUTPUT is explicitly unknown, never silently zero", () => {
  const c: Circuit = { version: 1, parts: [part("Y", "output")], wires: [] };
  const table = generated(c);
  assert.equal(table.hasUnknown, true);
  assert.deepEqual(table.rows, [{ inputs: [], outputs: [null] }]);
});

test("missing gate inputs preserve unknown rows and the simulator's known controlling values", () => {
  const c = binary("and");
  c.wires = c.wires.filter((w) => w.source !== "B");
  const table = generated(c);
  assert.deepEqual(table.rows.map((r) => r.outputs), [[0], [0], [null], [null]]);
  assert.equal(table.hasUnknown, true);
});

test("undefined one-hot encoder combinations remain unknown in the truth table", () => {
  const c = binary("and");
  c.parts[2].kind = "encoder";
  c.wires[0].targetPort = "D0";
  c.wires[1].targetPort = "D1";
  const table = generated(c);
  assert.deepEqual(table.rows.map((r) => r.outputs[0]), [null, 1, 0, null]);
  assert.equal(table.hasUnknown, true);
});

test("memory and clocks are rejected rather than passing off initial state as a truth table", () => {
  for (const kind of ["dff", "register", "counter", "clock"] as const) {
    const c: Circuit = { version: 1, parts: [part("memory", kind), part("Y", "output")], wires: [] };
    assert.deepEqual(truthTable(c), { ok: false, issue: kind === "clock" ? "clock" : "sequential", inputBits: 0 });
  }
});

test("static feedback detection catches self-loops and loops that the simulator settles to unknown", () => {
  const self: Circuit = {
    version: 1,
    parts: [part("g", "not"), part("Y", "output")],
    wires: [wire("g", "Y", "g", "A"), wire("g", "Y", "Y", "D")],
  };
  assert.deepEqual(truthTable(self), { ok: false, issue: "feedback", inputBits: 0 });
  self.parts.push(part("g2", "buffer"));
  self.wires[0] = wire("g2", "Y", "g", "A");
  self.wires.push(wire("g", "Y", "g2", "A"));
  assert.deepEqual(truthTable(self), { ok: false, issue: "feedback", inputBits: 0 });
});

test("invalid ports, missing endpoints, duplicate drivers and mismatched widths are blocked", () => {
  for (const mutate of [
    (c: Circuit) => { c.wires[0].sourcePort = "absent"; },
    (c: Circuit) => { c.wires[0].source = "absent"; },
    (c: Circuit) => { c.wires.push({ ...c.wires[0], id: "duplicate-driver" }); },
    (c: Circuit) => { c.parts[0].bits = 2; },
    (c: Circuit) => { c.parts[1].id = "A"; },
    (c: Circuit) => { c.parts[2].count = 0; },
    (c: Circuit) => { c.parts[2].bits = 0; },
  ]) {
    const c = binary("and");
    mutate(c);
    const result = truthTable(c);
    assert.equal(result.ok, false);
    if (!result.ok) assert.equal(result.issue, "invalid");
  }
});
