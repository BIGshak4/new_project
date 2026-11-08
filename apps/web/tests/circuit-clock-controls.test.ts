import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { emptyCircuit, makePart, type Kind } from "../src/lib/circuit";
import { tourSteps, stationReady } from "../src/lib/muxi-tour";

const require = createRequire(import.meta.url);
require.extensions[".css"] = module => { module.exports = {}; };

async function renderEditor(kinds: Kind[], readOnly = false) {
  const { default: CircuitEditor } = await import("../src/components/circuit-editor");
  const circuit = { ...emptyCircuit(), parts: kinds.map(makePart) };
  return renderToStaticMarkup(createElement(CircuitEditor, {
    value: circuit, lang: "en", readOnly,
    onChange: () => { throw new Error("Displaying signals must not edit the answer"); },
  }));
}

test("combinational drawings show live readings without offering clock controls", async () => {
  for (const readOnly of [false, true]) {
    const html = await renderEditor(["input", "nand", "output"], readOnly);
    assert.match(html, /Values on components and wires update/);
    assert.doesNotMatch(html, /data-muxi-control="circuit-(simulate|clock-step|reset)"/);
    assert.equal(html.includes("Connect pins without dragging"), !readOnly);
  }
  for (const kinds of [[], ["clock"]] as Kind[][]) {
    assert.doesNotMatch(await renderEditor(kinds), /data-muxi-control="circuit-simulate"/);
  }
});

test("flip-flops, registers and counters expose the clock session; merely opening it does not advance time", async () => {
  for (const kind of ["dff", "register", "counter"] as const) {
    const html = await renderEditor(["input", kind, "output"]);
    assert.match(html, /data-muxi-control="circuit-simulate"[^>]*aria-pressed="false"/);
    assert.doesNotMatch(html, /data-muxi-control="circuit-(clock-step|reset)"/);
  }
});

test("both guided circuits teach live input changes without requiring a clock", () => {
  for (const [kind, id, action] of [["preview", "guest-hardware", "drawing-tried"], ["member", "circuit", "input-toggled"]] as const) {
    const circuit = tourSteps(kind).find(step => step.id === id)!;
    assert.ok(stationReady(circuit, [action]));
    assert.equal(stationReady(circuit, ["circuit-simulated"]), false);
  }
});
