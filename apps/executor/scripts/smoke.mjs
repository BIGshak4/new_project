// Real, deployed compiler verification. This script makes no DB writes and is
// separate from mocked unit tests. It only submits repository smoke fixtures.
import { readFile } from "node:fs/promises";
import { createHash, createPrivateKey, randomUUID, sign } from "node:crypto";
import { CONTROL_TAMPER_FIXTURE } from "./control-tamper-fixture.mjs";

const base = process.env.JOBRUN_EXECUTOR_URL;
if (!base || new URL(base).protocol !== "https:") throw new Error("Set JOBRUN_EXECUTOR_URL to the deployed HTTPS executor.");
const seed = Buffer.from(process.env.JOBRUN_EXECUTION_SIGNING_SEED ?? "", "base64");
if (seed.length !== 32) throw new Error("Set the local-only JOBRUN_EXECUTION_SIGNING_SEED to the API's derived Ed25519 seed.");
const privateKey = createPrivateKey({ key: Buffer.concat([Buffer.from("302e020100300506032b657004220420", "hex"), seed]), type: "pkcs8", format: "der" });
const manifest = JSON.parse(await readFile(new URL("../../../backend/seeds/execution_cases.json", import.meta.url), "utf8"));
const fixtures = JSON.parse(await readFile(new URL("../../../backend/tests/fixtures/execution_smoke.json", import.meta.url), "utf8"));
const summary = [];
async function execute(job) {
  const job_json = JSON.stringify(job), stamp = Math.floor(Date.now() / 1000);
  const head = Buffer.from(JSON.stringify({ alg: "EdDSA", typ: "JWT" })).toString("base64url");
  const body = Buffer.from(JSON.stringify({ iss: "jobrun-api", aud: "jobrun-executor", sub: "00000000-0000-4000-8000-000000000001", jti: randomUUID(), iat: stamp, exp: stamp + 90, sha256: createHash("sha256").update(job_json).digest("hex") })).toString("base64url");
  const ticket = `${head}.${body}.${sign(null, Buffer.from(`${head}.${body}`), privateKey).toString("base64url")}`;
  const response = await fetch(new URL("/api/execute", base), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_json, ticket }), signal: AbortSignal.timeout(60000) });
  const raw = await response.text();
  if (Buffer.byteLength(raw) > 131072) throw new Error("The executor returned an oversized response.");
  if (!response.ok) throw new Error(`Executor HTTP ${response.status}: ${raw.slice(0, 512)}`);
  return JSON.parse(raw);
}
const health = await fetch(new URL("/api/health", base)).then(r => r.json());
if (!health.available) throw new Error("The live executor is not configured.");
for (const fixture of fixtures.cases) {
  const spec = manifest.questions[fixture.question_key]?.languages[fixture.language];
  if (!spec) throw new Error(`Missing smoke specification: ${fixture.question_key}/${fixture.language}`);
  for (const kind of ["correct", "wrong", "syntax_error"]) {
    const result = await execute({ language: fixture.language, source: fixture[kind], stdin: "", spec });
    const expected = kind === "correct" ? "passed" : kind === "wrong" ? "failed" : "compile_error";
    const row = { language: fixture.language, question: fixture.question_key, fixture: kind, expected, status: result.status, ok: result.status === expected, runtime_ms: result.runtime_ms, ...(result.status !== expected ? { detail: result.detail, compile_output: result.compile_output, stderr: result.stderr, cases: result.cases } : {}) };
    summary.push(row); console.log(JSON.stringify(row));
  }
}
for (const [name, source, expected] of [
  ["infinite-loop-timeout", "while True: pass\n", "timeout"],
  ["output-limit", "print('x' * 100000)\n", "runtime_error"],
  ["network-denied", "import socket\ntry:\n socket.create_connection(('1.1.1.1',443),timeout=0.5)\nexcept OSError:\n print('network-denied')\nelse:\n raise RuntimeError('Unexpected network access')\n", "completed"],
]) {
  const result = await execute({ language: "python", source, stdin: "" });
  const ok = result.status === expected && (name !== "network-denied" || result.stdout.trim() === "network-denied");
  const row = { fixture: name, expected, status: result.status, ok, runtime_ms: result.runtime_ms, ...(ok ? {} : { detail: result.detail, stdout: result.stdout, stderr: result.stderr }) };
  summary.push(row); console.log(JSON.stringify(row));
}
{
  const result = await execute(CONTROL_TAMPER_FIXTURE);
  const row = { fixture: "read-only-controls-and-sdk-write-symlinks", expected: "passed", status: result.status, ok: result.status === "passed" && result.passed_count === 2, runtime_ms: result.runtime_ms, ...(result.status === "passed" ? {} : { detail: result.detail, stderr: result.stderr, cases: result.cases }) };
  summary.push(row); console.log(JSON.stringify(row));
}
console.log(JSON.stringify({ live: true, executor: base, checked: summary.length, passed: summary.filter(r => r.ok).length, failed: summary.filter(r => !r.ok).length }));
if (summary.some(r => !r.ok)) process.exitCode = 1;
