import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { emptyCircuit, makePart, type Kind } from "../src/lib/circuit";
import { FULL_TOUR, SHORT_TOUR, stationReady } from "../src/lib/muxi-tour";

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

test("wired example completes the live-output station in both tours; sequential playback remains separate", () => {
  for (const tour of [SHORT_TOUR, FULL_TOUR]) {
    const live = tour.find(step => step.id === "simulate")!;
    assert.ok(stationReady(live, ["circuit-sample-loaded"]));
    assert.equal(stationReady(live, ["circuit-simulated"]), false);
  }
  assert.ok(stationReady(FULL_TOUR.find(step => step.id === "clock-start")!, ["circuit-simulated"]));
});
