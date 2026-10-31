import assert from "node:assert/strict";
import { afterEach, before, mock, test } from "node:test";
import { createRequire } from "node:module";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  ExecutionRequestGate,
  executionErrorMessage,
  executionInputKey,
  executionStatusLabel,
  type CodeExecutionResult,
} from "../src/lib/code-execution";

const require = createRequire(import.meta.url);
require.extensions[".css"] = (module) => { module.exports = {}; };
process.env.NEXT_PUBLIC_SUPABASE_URL = "https://execution-fixture.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "execution-fixture-key";
let client: typeof import("../src/lib/practice-api");
let supabase: (typeof import("../src/lib/supabase"))["supabase"];
let view: typeof import("../src/components/code-execution-panel");
before(async () => {
  client = await import("../src/lib/practice-api");
  ({ supabase } = await import("../src/lib/supabase"));
  view = await import("../src/components/code-execution-panel");
});
afterEach(() => mock.restoreAll());

const result = (patch: Partial<CodeExecutionResult> = {}): CodeExecutionResult => ({
  status: "completed", language: "c", compiled: true, executed: true, passed: null,
  stdout: "", stderr: "", compile_output: "", cases: [], runtime_ms: 12, detail: "", ...patch,
});

test("late execution replies cannot grade an edited draft or another attempt", () => {
  const gate = new ExecutionRequestGate();
  const original = executionInputKey("a", "python", "print(1)", "");
  const pending = gate.begin();
  assert.equal(gate.accepts(pending, original, original), true);
  for (const changed of [
    executionInputKey("a", "python", "print(2)", ""),
    executionInputKey("a", "javascript", "print(1)", ""),
    executionInputKey("b", "python", "print(1)", ""),
    executionInputKey("a", "python", "print(1)", "new input"),
  ]) assert.equal(gate.accepts(pending, original, changed), false);
  const next = gate.begin();
  assert.equal(gate.accepts(pending, original, original), false);
  assert.equal(gate.accepts(next, original, original), true);
  gate.invalidate();
  assert.equal(gate.accepts(next, original, original), false);
});

test("a successful program or HDL compile never claims a correct answer", () => {
  for (const lang of ["he", "en"] as const) {
    for (const candidate of [result(), result({ status: "compile_only", executed: false })]) {
      const html = renderToStaticMarkup(createElement(view.ExecutionResultView, { result: candidate, lang }));
      assert.match(html, lang === "he" ? /נכונות: לא נבדקה/ : /Correctness: not assessed/);
      assert.doesNotMatch(html, /כל הבדיקות שהוגדרו עברו|All configured tests passed/);
      assert.match(html, /role="status"/);
    }
    assert.match(executionStatusLabel(result({ status: "passed", passed: true }), lang), lang === "he" ? /הבדיקות שהוגדרו עברו/ : /configured tests passed/);
  }
});

test("compiler output, stderr and testcase values are inert text in both languages", () => {
  const payload = '<img src=x onerror="alert(1)"><script>bad()</script>';
  for (const lang of ["he", "en"] as const) {
    const html = renderToStaticMarkup(createElement(view.ExecutionResultView, {
      result: result({ status: "failed", passed: false, stdout: payload, stderr: payload, compile_output: payload, detail: payload, cases: [{ index: 0, passed: false, input: payload, expected: payload, actual: payload }] }),
      lang,
      stale: true,
    }));
    assert.doesNotMatch(html, /<script\b|<img\b/);
    assert.match(html, /&lt;script&gt;/);
    assert.match(html, /dir="ltr"/);
    assert.match(html, /tabindex="0"/);
    assert.match(html, lang === "he" ? /התוצאה הזאת שייכת לגרסה הקודמת/ : /result belongs to the previous version/);
  }
});

test("saved evaluation renders its authoritative execution once instead of legacy test rows", async () => {
  const { EvaluationPanel } = await import("../src/components/evaluation-panel");
  const submission = {
    status: "done", band: "PARTIAL", flags: [], evidence: "full", key_points_hit: [], key_points_missed: [],
    summary: "review", card: null, tip: null, assessed_by: "model", model: null,
    check: { type: "code_tests", passed: false, detail: "compiled execution", mismatches: [{ inputs: "LEGACY_DUPLICATE", expected: 1, got: 2 }], execution: result({ status: "failed", passed: false, cases: [{ index: 0, passed: false, input: [1], expected: 2, actual: 3 }] }) },
  } as unknown as import("../src/lib/practice-api").Submission;
  for (const lang of ["he", "en"] as const) {
    const html = renderToStaticMarkup(createElement(EvaluationPanel, { submission, lang }));
    assert.equal((html.match(/data-execution-status="failed"/g) ?? []).length, 1);
    assert.doesNotMatch(html, /LEGACY_DUPLICATE|mismatch-table/);
    assert.match(html, lang === "he" ? /הבדיקות שהוגדרו נכשלו/ : /configured tests failed/);
  }
});

test("test totals use server counts rather than the bounded diagnostic sample", () => {
  const candidate = result({ status: "failed", passed: false, test_count: 256, passed_count: 255, cases: [{ index: 181, passed: false, expected: 1, actual: 0 }] });
  for (const lang of ["he", "en"] as const) {
    const html = renderToStaticMarkup(createElement(view.ExecutionResultView, { result: candidate, lang }));
    assert.match(html, /<bdi dir="ltr">255\/256<\/bdi>/);
    assert.match(html, lang === "he" ? /דוגמאות מתוצאות הבדיקה/ : /Sample test results/);
    assert.match(html, lang === "he" ? /מקרה 181:/ : /Case 181:/);
    assert.doesNotMatch(html, />0\/1<|>255\/1<|>1\/1</);
  }
  const legacy = renderToStaticMarkup(createElement(view.ExecutionResultView, { result: result(), lang: "en" }));
  assert.doesNotMatch(legacy, /undefined|NaN|defined tests passed/);
});

test("execution posts only draft inputs to its owned attempt, with auth and idempotency", async () => {
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "fixture-access" } }, error: null }));
  const requests: { url: string; init: RequestInit }[] = [];
  mock.method(globalThis, "fetch", async (url: string, init: RequestInit) => { requests.push({ url, init }); return Response.json(result()); });
  const body = { language: "python", source: "print(1)", stdin: "", idempotency_key: "same-run" };
  await client.practiceApi("https://api.example").executeCode("owned/attempt", body);
  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, "https://api.example/v1/practice/attempts/owned%2Fattempt/executions");
  assert.deepEqual(JSON.parse(requests[0].init.body as string), body);
  assert.equal((requests[0].init.headers as Record<string, string>).Authorization, "Bearer fixture-access");
  assert.equal((requests[0].init.headers as Record<string, string>)["Idempotency-Key"], "same-run");
  assert.ok(!requests[0].url.includes("submissions"));
});

test("cancelling an execution reaches fetch and does not retry or turn into a network failure", async () => {
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "fixture-access" } }, error: null }));
  const controller = new AbortController();
  const abort = new DOMException("cancelled", "AbortError");
  const fetch = mock.method(globalThis, "fetch", async (_url: string, init: RequestInit) => {
    controller.abort();
    assert.equal(init.signal?.aborted, true);
    throw abort;
  });
  await assert.rejects(client.practiceApi("https://api.example").executeCode("a", { language: "python", source: "print(1)", stdin: "", idempotency_key: "k" }, controller.signal), (issue) => issue === abort);
  assert.equal(fetch.mock.callCount(), 1);
});

test("execution quotas and session expiry have specific recovery messages", () => {
  for (const lang of ["he", "en"] as const) {
    assert.match(executionErrorMessage({ status: 429 }, lang), lang === "he" ? /מגבלת ההרצות/ : /execution limit/);
    assert.match(executionErrorMessage({ status: 401 }, lang), lang === "he" ? /ההתחברות פגה/ : /session expired/);
    assert.match(executionErrorMessage({ status: 422 }, lang), lang === "he" ? /מגבלות גודל/ : /size limits/);
  }
});
