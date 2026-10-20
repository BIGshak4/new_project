import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { test } from "node:test";
import vm from "node:vm";

// Extract the production pure helpers so this regression needs neither browser
// credentials nor the Supabase singleton imported by the component module.
const require = createRequire(new URL("../../apps/tasks/package.json", import.meta.url));
const ts = require("typescript");
const source = readFileSync(new URL("../../apps/tasks/src/components/admin-support.tsx", import.meta.url), "utf8");
const ast = ts.createSourceFile("admin-support.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const names = new Set(["handling", "reconcileReplyHandling"]);
const helpers = ast.statements
  .filter((node) => ts.isFunctionDeclaration(node) && names.has(node.name?.text))
  .map((node) => node.getText(ast));
assert.equal(helpers.length, names.size, "The production reconciliation helpers must remain available to the regression.");
const exports = {};
const compiled = ts.transpileModule(helpers.join("\n"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
vm.runInNewContext(compiled, { exports, JSON }, { filename: "admin-support-reconciliation.js" });
const reconcile = exports.reconcileReplyHandling;
assert.equal(typeof reconcile, "function");

const report = {
  id: "report", version: 1, status: "open", priority: "normal", assigned_to: null,
  internal_notes: "Original note", resolution: "",
};
const clean = {
  status: report.status, priority: report.priority, assigned_to: null,
  internal_notes: report.internal_notes, resolution: "",
};
// Reply v1 committed but its response was lost. Another founder then changed
// handling before the idempotent retry returned the current report at v3.
const concurrent = {
  ...report, version: 3, status: "in_progress", priority: "high",
  internal_notes: "Another founder investigated",
};

test("recovered reply synchronizes a clean v1 draft to concurrent v3 handling", () => {
  const next = reconcile(report, clean, concurrent);
  assert.equal(next.report.version, 3);
  assert.equal(next.conflict, false);
  assert.deepEqual(JSON.parse(JSON.stringify(next.draft)), {
    status: concurrent.status, priority: concurrent.priority, assigned_to: null,
    internal_notes: concurrent.internal_notes, resolution: "",
  });
});

test("recovered reply retains a dirty v1 draft and original expected version when handling changed", () => {
  const draft = { ...clean, internal_notes: "My unsaved investigation" };
  const next = reconcile(report, draft, concurrent);
  assert.equal(next.report, report);
  assert.equal(next.report.version, 1);
  assert.equal(next.draft, draft);
  assert.equal(next.conflict, true);
});

test("a reply-only version bump preserves dirty handling when server fields are unchanged", () => {
  const draft = { ...clean, priority: "high" };
  const next = reconcile(report, draft, { ...report, version: 2 });
  assert.equal(next.report.version, 2);
  assert.equal(next.draft, draft);
  assert.equal(next.conflict, false);
});

test("concurrent assignment, resolution and priority changes also require comparison", () => {
  const draft = { ...clean, internal_notes: "My draft" };
  for (const change of [
    { assigned_to: "other-founder" },
    { resolution: "A concurrent public explanation" },
    { priority: "high" },
  ]) {
    const next = reconcile(report, draft, { ...report, ...change, version: 3 });
    assert.equal(next.report.version, 1);
    assert.equal(next.draft, draft);
    assert.equal(next.conflict, true);
  }
});
