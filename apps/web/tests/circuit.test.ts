import test from "node:test";
import assert from "node:assert/strict";
import {
  simulate,
  ports,
  reconfigure,
  connectionError,
  KINDS,
  type Circuit,
  type Part,
  type Kind,
} from "../src/lib/circuit";

function part(id: string, kind: Kind, patch: Partial<Part> = {}): Part {
  return {
    id,
    kind,
    label: id,
    x: 0,
    y: 0,
    count: 2,
    bits: 1,
    value: 0,
    ...patch,
  };
}
function fixture(
  kind: Kind,
  values: Record<string, number>,
  patch: Partial<Part> = {},
): Circuit {
  const gate = part("g", kind, patch),
    pins = ports(gate);
  return {
    version: 1,
    parts: [
      gate,
      ...Object.entries(values).map(([id, value]) =>
        part(id, "input", {
          value,
          bits: pins.inputs.find((p) => p.id === id)!.bits,
        }),
      ),
    ],
    wires: Object.keys(values).map((id) => ({
      id,
      source: id,
      sourcePort: "Q",
      target: "g",
      targetPort: id,
    })),
  };
}
const out = (c: Circuit, name = "Y") => simulate(c).signals[`g:${name}`];

test("truth tables for all binary gates, NOT and buffer", () => {
  for (const a of [0, 1])
    for (const b of [0, 1]) {
      for (const [kind, expected] of Object.entries({
        and: a & b,
        or: a | b,
        xor: a ^ b,
        nand: 1 - (a & b),
        nor: 1 - (a | b),
        xnor: 1 - (a ^ b),
      }))
        assert.equal(
          out(fixture(kind as Kind, { A0: a, A1: b })),
          expected,
          kind,
        );
      assert.equal(out(fixture("not", { A: a })), 1 - a);
      assert.equal(out(fixture("buffer", { A: a })), a);
    }
});
test("MUX chooses only the selected input, demux and decoder route each line", () => {
  for (let s = 0; s < 4; s++) {
    assert.equal(
      out(fixture("mux", { [`D${s}`]: 7, S: s }, { count: 4, bits: 3 })),
      7,
    );
    const demux = simulate(
      fixture("demux", { D: 5, S: s }, { count: 4, bits: 3 }),
    );
    const decoder = simulate(fixture("decoder", { A: s }, { count: 4 }));
    for (let i = 0; i < 4; i++) {
      assert.equal(demux.signals[`g:Y${i}`], i === s ? 5 : 0);
      assert.equal(decoder.signals[`g:Y${i}`], Number(i === s));
    }
  }
});
test("one-hot encoder treats ambiguous input as unknown", () => {
  for (let s = 0; s < 4; s++)
    assert.equal(
      out(
        fixture(
          "encoder",
          Object.fromEntries(
            Array.from({ length: 4 }, (_, i) => [`D${i}`, Number(s === i)]),
          ),
          { count: 4 },
        ),
      ),
      s,
    );
  assert.equal(out(fixture("encoder", { D0: 1, D1: 1 })), null);
  assert.equal(out(fixture("encoder", { D0: 0, D1: 0 }), "V"), 0);
});
test("adders: exhaustive one-bit arithmetic and multi-bit overflow", () => {
  for (let a = 0; a < 2; a++)
    for (let b = 0; b < 2; b++)
      for (let cin = 0; cin < 2; cin++) {
        const c = fixture("full-adder", { A: a, B: b, Cin: cin });
        assert.equal(out(c, "S"), (a + b + cin) & 1);
        assert.equal(out(c, "Cout"), (a + b + cin) >> 1);
        const h = fixture("half-adder", { A: a, B: b });
        assert.equal(out(h, "S"), a ^ b);
        assert.equal(out(h, "C"), a & b);
      }
  for (const bits of [4, 8, 16]) {
    const c = fixture("adder", { A: 2 ** bits - 1, B: 1, Cin: 0 }, { bits });
    assert.equal(out(c, "S"), 0);
    assert.equal(out(c, "Cout"), 1);
  }
});
test("splitter/joiner ordering is least-significant-bit first", () => {
  const c = fixture("splitter", { D: 10 }, { bits: 4 });
  const s = simulate(c);
  assert.deepEqual(
    [0, 1, 2, 3].map((i) => s.signals[`g:B${i}`]),
    [0, 1, 0, 1],
  );
  assert.equal(
    out(fixture("joiner", { B0: 0, B1: 1, B2: 0, B3: 1 }, { bits: 4 })),
    10,
  );
});
test("unsigned comparator and sixteen-bit masking", () => {
  for (const a of [0, 1, 65535])
    for (const b of [0, 1, 65535]) {
      const c = fixture("comparator", { A: a, B: b }, { bits: 16 });
      assert.equal(out(c, "EQ"), Number(a === b));
      assert.equal(out(c, "LT"), Number(a < b));
      assert.equal(out(c, "GT"), Number(a > b));
    }
  assert.equal(out(fixture("not", { A: 0 }, { bits: 16 })), 65535);
});
test("register samples only rising edges, holds on edits, asynchronous reset", () => {
  const c = fixture("register", { D: 5, RST: 0 }, { bits: 4 });
  c.parts.push(part("clock", "clock"));
  c.wires.push({
    id: "clk",
    source: "clock",
    sourcePort: "Q",
    target: "g",
    targetPort: "CLK",
  });
  let s = simulate(c);
  assert.equal(s.signals["g:Q"], 0);
  s = simulate(c, s, 1);
  assert.equal(s.signals["g:Q"], 5);
  c.parts.find((p) => p.id === "D")!.value = 9;
  s = simulate(c, s, 1);
  assert.equal(s.signals["g:Q"], 5);
  s = simulate(c, s, 0);
  s = simulate(c, s, 1);
  assert.equal(s.signals["g:Q"], 9);
  c.parts.find((p) => p.id === "RST")!.value = 1;
  assert.equal(simulate(c, s).signals["g:Q"], 0);
});
test("counter enable, overflow, and simultaneous register sampling", () => {
  const c = fixture("counter", { EN: 1 }, { bits: 2 });
  c.parts.push(part("clk", "clock"));
  c.wires.push({
    id: "clock",
    source: "clk",
    sourcePort: "Q",
    target: "g",
    targetPort: "CLK",
  });
  let s = simulate(c);
  for (let i = 1; i <= 5; i++) {
    s = simulate(c, s, 1);
    assert.equal(s.signals["g:Q"], i % 4);
    s = simulate(c, s, 0);
  }
  c.parts.find((p) => p.id === "EN")!.value = 0;
  assert.equal(simulate(c, s, 1).signals["g:Q"], 1);
  const d = fixture("dff", { D: 1 });
  d.parts.push(part("clk", "clock"), part("q2", "dff"));
  d.wires.push(
    {
      id: "c1",
      source: "clk",
      sourcePort: "Q",
      target: "g",
      targetPort: "CLK",
    },
    {
      id: "c2",
      source: "clk",
      sourcePort: "Q",
      target: "q2",
      targetPort: "CLK",
    },
    { id: "q", source: "g", sourcePort: "Q", target: "q2", targetPort: "D" },
  );
  let v = simulate(d);
  v = simulate(d, v, 1);
  assert.equal(v.signals["g:Q"], 1);
  assert.equal(v.signals["q2:Q"], 0);
});
test("unknowns, cycles and wrong-width/duplicate-driver connections stay explicit", () => {
  assert.equal(out(fixture("xor", { A0: 1 })), null);
  const c = fixture("and", { A0: 1, A1: 0 });
  const wire = c.wires[0];
  assert.equal(connectionError(c, wire), "occupied");
  const changed = reconfigure(c, { ...c.parts[0], bits: 4 });
  assert.equal(changed.wires.length, 0);
  assert.equal(connectionError(changed, wire), "width");
  const cycle: Circuit = {
    version: 1,
    parts: [part("g", "not")],
    wires: [
      {
        id: "loop",
        source: "g",
        sourcePort: "Y",
        target: "g",
        targetPort: "A",
      },
    ],
  };
  assert.equal(out(cycle), null);
  for (const kind of KINDS)
    assert.doesNotThrow(() =>
      simulate({ version: 1, parts: [part("g", kind)], wires: [] }),
    );
});

test("derived clocks stay unassessed and resized registers cannot retain out-of-range bits", () => {
  const c = fixture("register", { D: 15, CLK: 0 }, { bits: 4 });
  let s = simulate(c);
  c.parts.find((p) => p.id === "CLK")!.value = 1;
  s = simulate(c, s);
  assert.equal(s.signals["g:Q"], 15);
  const resized = reconfigure(c, { ...c.parts[0], bits: 2 });
  assert.equal(simulate(resized, s).signals["g:Q"], 3);

  c.parts.push(part("buffer", "buffer"));
  c.wires = c.wires.filter((w) => w.targetPort !== "CLK");
  c.wires.push(
    {
      id: "in",
      source: "CLK",
      sourcePort: "Q",
      target: "buffer",
      targetPort: "A",
    },
    {
      id: "derived",
      source: "buffer",
      sourcePort: "Y",
      target: "g",
      targetPort: "CLK",
    },
  );
  const unsupported = simulate(c, s);
  assert.deepEqual(unsupported.unsupportedClocks, ["g"]);
  assert.equal(unsupported.signals["g:Q"], null);

  const d = fixture("dff", { D: 1 });
  const unknownClock = simulate(d);
  d.parts.push(part("clk", "input", { value: 1 }));
  d.wires.push({
    id: "new",
    source: "clk",
    sourcePort: "Q",
    target: "g",
    targetPort: "CLK",
  });
  // Connecting a high input after an unknown clock is not a proven rising edge.
  assert.equal(simulate(d, unknownClock).signals["g:Q"], 0);
});
