/** Portable circuit format. No React Flow or simulation state is persisted. */
export const KINDS = [
  "input",
  "output",
  "constant",
  "clock",
  "and",
  "nand",
  "or",
  "nor",
  "xor",
  "xnor",
  "not",
  "buffer",
  "mux",
  "demux",
  "encoder",
  "decoder",
  "half-adder",
  "full-adder",
  "adder",
  "comparator",
  "dff",
  "register",
  "counter",
  "splitter",
  "joiner",
] as const;
export type Kind = (typeof KINDS)[number];
export type Part = {
  id: string;
  kind: Kind;
  label: string;
  x: number;
  y: number;
  count: number;
  bits: number;
  value: number;
};
export type Wire = {
  id: string;
  source: string;
  sourcePort: string;
  target: string;
  targetPort: string;
};
export type Circuit = { version: 1; parts: Part[]; wires: Wire[] };
export type AnswerImage = {
  path: string;
  name: string;
  mime: "image/jpeg" | "image/png" | "image/webp";
  size: number;
};
export type VisualAnswer = { circuit: Circuit | null; images: AnswerImage[] };
export const emptyVisual = (): VisualAnswer => ({ circuit: null, images: [] });
export const emptyCircuit = (): Circuit => ({
  version: 1,
  parts: [],
  wires: [],
});
export const hasVisual = (v?: VisualAnswer | null) =>
  !!(v?.circuit?.parts.length || v?.images.length);
export const hasCount = (kind: Kind) =>
  [
    "and",
    "nand",
    "or",
    "nor",
    "xor",
    "xnor",
    "mux",
    "demux",
    "encoder",
    "decoder",
  ].includes(kind);
export const powerCount = (kind: Kind) =>
  ["mux", "demux", "encoder", "decoder"].includes(kind);
export const sequential = (kind: Kind) =>
  ["dff", "register", "counter"].includes(kind);
export const mask = (bits: number) => 2 ** bits - 1;
export function makePart(kind: Kind, index: number): Part {
  return {
    id: crypto.randomUUID(),
    kind,
    label: kind.toUpperCase(),
    x: (index % 3) * 220,
    y: Math.floor(index / 3) * 190,
    count: 2,
    bits: 1,
    value: 0,
  };
}
export type Port = { id: string; label: string; bits: number };
export function ports(p: Part): { inputs: Port[]; outputs: Port[] } {
  const port = (id: string, bits = p.bits, label = id): Port => ({
    id,
    bits,
    label,
  });
  const many = (prefix: string, n: number, bits = p.bits) =>
    Array.from({ length: n }, (_, i) => port(`${prefix}${i}`, bits));
  const selectBits = Math.log2(p.count);
  switch (p.kind) {
    case "input":
    case "constant":
      return { inputs: [], outputs: [port("Q")] };
    case "clock":
      return { inputs: [], outputs: [port("Q", 1)] };
    case "output":
      return { inputs: [port("D")], outputs: [] };
    case "not":
    case "buffer":
      return { inputs: [port("A")], outputs: [port("Y")] };
    case "mux":
      return {
        inputs: [...many("D", p.count), port("S", selectBits)],
        outputs: [port("Y")],
      };
    case "demux":
      return {
        inputs: [port("D"), port("S", selectBits)],
        outputs: many("Y", p.count),
      };
    case "encoder":
      return {
        inputs: many("D", p.count, 1),
        outputs: [port("Y", selectBits), port("V", 1)],
      };
    case "decoder":
      return {
        inputs: [port("A", selectBits)],
        outputs: many("Y", p.count, 1),
      };
    case "half-adder":
      return {
        inputs: [port("A", 1), port("B", 1)],
        outputs: [port("S", 1), port("C", 1)],
      };
    case "full-adder":
      return {
        inputs: [port("A", 1), port("B", 1), port("Cin", 1)],
        outputs: [port("S", 1), port("Cout", 1)],
      };
    case "adder":
      return {
        inputs: [port("A"), port("B"), port("Cin", 1)],
        outputs: [port("S"), port("Cout", 1)],
      };
    case "comparator":
      return {
        inputs: [port("A"), port("B")],
        outputs: [port("GT", 1, ">"), port("EQ", 1, "="), port("LT", 1, "<")],
      };
    case "dff":
    case "register":
      return {
        inputs: [port("D"), port("CLK", 1), port("RST", 1)],
        outputs: [port("Q"), port("QN")],
      };
    case "counter":
      return {
        inputs: [port("EN", 1), port("CLK", 1), port("RST", 1)],
        outputs: [port("Q")],
      };
    case "splitter":
      return { inputs: [port("D")], outputs: many("B", p.bits, 1) };
    case "joiner":
      return { inputs: many("B", p.bits, 1), outputs: [port("Y")] };
    default:
      return { inputs: many("A", p.count), outputs: [port("Y")] };
  }
}
export function connectionError(
  c: Circuit,
  w: Omit<Wire, "id">,
): "missing" | "width" | "occupied" | null {
  const from = c.parts.find((p) => p.id === w.source),
    to = c.parts.find((p) => p.id === w.target);
  const a = from && ports(from).outputs.find((p) => p.id === w.sourcePort);
  const b = to && ports(to).inputs.find((p) => p.id === w.targetPort);
  if (!a || !b) return "missing";
  if (a.bits !== b.bits) return "width";
  if (
    c.wires.some((e) => e.target === w.target && e.targetPort === w.targetPort)
  )
    return "occupied";
  return null;
}
export function reconfigure(c: Circuit, part: Part): Circuit {
  const next = {
    ...c,
    parts: c.parts.map((p) => (p.id === part.id ? part : p)),
    wires: [] as Wire[],
  };
  for (const w of c.wires) if (!connectionError(next, w)) next.wires.push(w);
  return next;
}
export type Signal = number | null;
export type Simulation = {
  signals: Record<string, Signal>;
  memory: Record<string, Signal>;
  clocks: Record<string, Signal>;
  clock: 0 | 1;
  unstable: boolean;
  unsupportedClocks: string[];
};
export const signalKey = (id: string, port: string) => `${id}:${port}`;
export function simulate(
  c: Circuit,
  previous?: Simulation,
  clock: 0 | 1 = previous?.clock ?? 0,
): Simulation {
  const memory = Object.fromEntries(
    c.parts
      .filter((p) => sequential(p.kind))
      .map((p) => [
        p.id,
        previous && p.id in previous.memory
          ? previous.memory[p.id] === null
            ? null
            : previous.memory[p.id]! & mask(p.bits)
          : 0,
      ]),
  );
  const unsupportedClocks = c.parts
    .filter((p) => sequential(p.kind))
    .filter((p) => {
      const w = c.wires.find(
        (w) => w.target === p.id && w.targetPort === "CLK",
      );
      const driver = c.parts.find((n) => n.id === w?.source);
      return driver && !["clock", "input", "constant"].includes(driver.kind);
    })
    .map((p) => p.id);
  for (const id of unsupportedClocks) memory[id] = null;
  const incoming = new Map(
    c.wires.map((w) => [signalKey(w.target, w.targetPort), w]),
  );
  const pinSets = new Map(c.parts.map((p) => [p.id, ports(p)]));
  const settle = () => {
    let values: Record<string, Signal> = {};
    const read = (
      p: Part,
      port: string,
      defaultValue: Signal = null,
    ): Signal => {
      const w = incoming.get(signalKey(p.id, port));
      return w
        ? (values[signalKey(w.source, w.sourcePort)] ?? null)
        : defaultValue;
    };
    let stable = false;
    for (let step = 0; step < c.parts.length * 2 + 4; step++) {
      const next: Record<string, Signal> = {};
      for (const p of c.parts) {
        const put = (port: string, value: Signal) => {
          next[signalKey(p.id, port)] = value;
        };
        const ins = pinSets
          .get(p.id)!
          .inputs.map((i) =>
            read(p, i.id, ["RST", "Cin"].includes(i.id) ? 0 : null),
          );
        const known = ins.every((v) => v !== null),
          v = ins as number[],
          m = mask(p.bits);
        for (const out of pinSets.get(p.id)!.outputs) put(out.id, null);
        switch (p.kind) {
          case "input":
          case "constant":
            put("Q", p.value & m);
            break;
          case "clock":
            put("Q", clock);
            break;
          case "output":
            put("display", read(p, "D"));
            break;
          case "dff":
          case "register":
            put("Q", memory[p.id]);
            put("QN", memory[p.id] === null ? null : ~memory[p.id]! & m);
            break;
          case "counter":
            put("Q", memory[p.id]);
            break;
          case "mux": {
            const s = read(p, "S");
            put("Y", s === null ? null : read(p, `D${s}`));
            break;
          }
          case "demux": {
            const s = read(p, "S");
            for (let i = 0; i < p.count; i++)
              put(`Y${i}`, s === null ? null : s === i ? read(p, "D") : 0);
            break;
          }
          case "encoder": {
            // Strict one-hot encoder: V=0 for no asserted input, unknown for multiple asserted inputs.
            if (known) {
              const active = v.flatMap((n, i) => (n ? [i] : []));
              put("V", active.length <= 1 ? Number(active.length === 1) : null);
              put("Y", active.length === 1 ? active[0] : null);
            }
            break;
          }
          case "decoder":
            if (known)
              for (let i = 0; i < p.count; i++)
                put(`Y${i}`, Number(v[0] === i));
            break;
          case "splitter":
            if (known)
              for (let i = 0; i < p.bits; i++) put(`B${i}`, (v[0] >> i) & 1);
            break;
          case "joiner":
            if (known)
              put(
                "Y",
                v.reduce((a, n, i) => a | (n << i), 0),
              );
            break;
          case "half-adder":
          case "full-adder":
          case "adder":
            if (known) {
              const bits = p.kind === "adder" ? p.bits : 1,
                sum = v.reduce((a, n) => a + n, 0);
              put("S", sum & mask(bits));
              put(
                p.kind === "half-adder" ? "C" : "Cout",
                Number(sum > mask(bits)),
              );
            }
            break;
          case "comparator":
            if (known) {
              put("GT", Number(v[0] > v[1]));
              put("EQ", Number(v[0] === v[1]));
              put("LT", Number(v[0] < v[1]));
            }
            break;
          case "not":
          case "buffer":
            if (known) put("Y", p.kind === "not" ? ~v[0] & m : v[0]);
            break;
          default: {
            // Conservative unknown propagation, except controlling all-zero/all-one inputs.
            let result: Signal = null;
            if (["and", "nand"].includes(p.kind))
              result = ins.includes(0)
                ? 0
                : known
                  ? v.reduce((a, b) => a & b, m)
                  : null;
            else if (["or", "nor"].includes(p.kind))
              result = ins.includes(m)
                ? m
                : known
                  ? v.reduce((a, b) => a | b, 0)
                  : null;
            else if (known) result = v.reduce((a, b) => a ^ b, 0);
            if (result !== null && ["nand", "nor", "xnor"].includes(p.kind))
              result = ~result & m;
            put("Y", result);
          }
        }
      }
      stable = Object.keys(next).every((k) => next[k] === values[k]);
      values = next;
      if (stable) break;
    }
    return { values, read, stable };
  };
  let settled = settle();
  const clocks: Record<string, Signal> = {};
  // All registers sample the same pre-edge values (no ordering-dependent ripple).
  const updated = { ...memory };
  for (const p of c.parts.filter((p) => sequential(p.kind))) {
    const clk = settled.read(p, "CLK"),
      rst = settled.read(p, "RST", 0);
    clocks[p.id] = clk;
    if (unsupportedClocks.includes(p.id)) updated[p.id] = null;
    else if (rst === 1) updated[p.id] = 0;
    else if (rst === null) updated[p.id] = null;
    else if (
      clk === 1 &&
      (previous && p.id in previous.clocks ? previous.clocks[p.id] : 0) === 0
    ) {
      const data = settled.read(p, p.kind === "counter" ? "EN" : "D");
      updated[p.id] =
        p.kind !== "counter"
          ? data
          : data === null
            ? null
            : data === 0
              ? memory[p.id]
              : memory[p.id] === null
                ? null
                : (memory[p.id]! + 1) & mask(p.bits);
    }
  }
  Object.assign(memory, updated);
  settled = settle();
  return {
    signals: settled.values,
    memory,
    clocks,
    clock,
    unstable: !settled.stable,
    unsupportedClocks,
  };
}

export const MAX_TRUTH_TABLE_INPUT_BITS = 6;
export type TruthTableIssue =
  | "empty"
  | "invalid"
  | "sequential"
  | "clock"
  | "no-output"
  | "too-many-inputs"
  | "feedback";
export type TruthTableColumn = { id: string; label: string; bits: number };
export type TruthTablePlan =
  | { ok: false; issue: TruthTableIssue; inputBits: number }
  | {
      ok: true;
      inputs: TruthTableColumn[];
      outputs: TruthTableColumn[];
      inputBits: number;
    };
export type TruthTable = Extract<TruthTablePlan, { ok: true }> & {
  rows: { inputs: number[]; outputs: Signal[] }[];
  hasUnknown: boolean;
};

/** Check eligibility without running the simulator or changing the drawing. */
export function truthTablePlan(c: Circuit): TruthTablePlan {
  const inputBits = c.parts
    .filter((p) => p.kind === "input")
    .reduce((n, p) => n + p.bits, 0);
  const issue = (reason: TruthTableIssue): TruthTablePlan => ({
    ok: false,
    issue: reason,
    inputBits,
  });
  if (!c.parts.length) return issue("empty");
  const seenParts = new Set<string>();
  if (
    c.version !== 1 ||
    c.parts.length > 100 ||
    c.wires.length > 200 ||
    c.parts.some((p) => {
      const repeated = seenParts.has(p.id);
      seenParts.add(p.id);
      return (
        repeated ||
        !KINDS.includes(p.kind) ||
        !Number.isInteger(p.bits) ||
        p.bits < 1 ||
        p.bits > 16 ||
        !Number.isInteger(p.value) ||
        (hasCount(p.kind) &&
          (!Number.isInteger(p.count) ||
            p.count < 2 ||
            p.count > 16 ||
            (powerCount(p.kind) && ![2, 4, 8, 16].includes(p.count))))
      );
    })
  )
    return issue("invalid");
  const connected: Circuit = { ...c, wires: [] };
  const seenWires = new Set<string>();
  for (const w of c.wires) {
    if (seenWires.has(w.id) || connectionError(connected, w))
      return issue("invalid");
    seenWires.add(w.id);
    connected.wires.push(w);
  }
  if (c.parts.some((p) => sequential(p.kind))) return issue("sequential");
  if (c.parts.some((p) => p.kind === "clock")) return issue("clock");
  if (!c.parts.some((p) => p.kind === "output")) return issue("no-output");
  if (inputBits > MAX_TRUTH_TABLE_INPUT_BITS) return issue("too-many-inputs");

  // A feedback loop can settle to ? and still look "stable" to a zero-delay
  // simulator. Detect topology explicitly rather than treating that as logic.
  const next = new Map(c.parts.map((p) => [p.id, [] as string[]]));
  for (const w of c.wires) next.get(w.source)!.push(w.target);
  const visiting = new Set<string>(),
    visited = new Set<string>();
  const cyclic = (id: string): boolean => {
    if (visiting.has(id)) return true;
    if (visited.has(id)) return false;
    visiting.add(id);
    if (next.get(id)!.some(cyclic)) return true;
    visiting.delete(id);
    visited.add(id);
    return false;
  };
  if (c.parts.some((p) => cyclic(p.id))) return issue("feedback");
  const column = (p: Part): TruthTableColumn => ({
    id: p.id,
    label: p.label,
    bits: p.bits,
  });
  return {
    ok: true,
    inputBits,
    inputs: c.parts.filter((p) => p.kind === "input").map(column),
    outputs: c.parts.filter((p) => p.kind === "output").map(column),
  };
}

/** Enumerate at most 64 combinations through the existing logic simulator. */
export function truthTable(
  c: Circuit,
): TruthTable | Extract<TruthTablePlan, { ok: false }> {
  const plan = truthTablePlan(c);
  if (!plan.ok) return plan;
  const rows: TruthTable["rows"] = [];
  let hasUnknown = false;
  for (let combination = 0; combination < 2 ** plan.inputBits; combination++) {
    let remaining = plan.inputBits;
    const inputs = plan.inputs.map((p) => {
      remaining -= p.bits;
      return (combination >> remaining) & mask(p.bits);
    });
    const values = new Map(plan.inputs.map((p, i) => [p.id, inputs[i]]));
    const result = simulate({
      ...c,
      parts: c.parts.map((p) =>
        p.kind === "input" ? { ...p, value: values.get(p.id)! } : p,
      ),
    });
    const outputs = plan.outputs.map((p) =>
      result.unstable ? null : (result.signals[signalKey(p.id, "display")] ?? null),
    );
    if (outputs.some((v) => v === null)) hasUnknown = true;
    rows.push({ inputs, outputs });
  }
  return { ...plan, rows, hasUnknown };
}
