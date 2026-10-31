// Real deployed execution of every committed algorithmic positive fixture.
// Sequential by design: leaves one broker slot available for browser validation.
// Operator signing material remains only in this process and never enters a VM.
import { readFile, writeFile } from "node:fs/promises";
import { createHash, createPrivateKey, randomUUID, sign } from "node:crypto";

const base = process.env.JOBRUN_EXECUTOR_URL;
if (!base || new URL(base).protocol !== "https:") throw new Error("Set JOBRUN_EXECUTOR_URL to the deployed HTTPS executor.");
const seed = Buffer.from(process.env.JOBRUN_EXECUTION_SIGNING_SEED ?? "", "base64");
if (seed.length !== 32) throw new Error("Set the local-only JOBRUN_EXECUTION_SIGNING_SEED to the API's derived Ed25519 seed.");
const privateKey = createPrivateKey({ key: Buffer.concat([Buffer.from("302e020100300506032b657004220420", "hex"), seed]), type: "pkcs8", format: "der" });
const manifest = JSON.parse(await readFile(new URL("../../../backend/seeds/execution_cases.json", import.meta.url), "utf8"));
const fixtures = JSON.parse(await readFile(new URL("../../../backend/tests/fixtures/execution_positive.json", import.meta.url), "utf8"));
const expectedPairs = new Set(Object.entries(manifest.questions).flatMap(([question, record]) => Object.keys(record.languages).map(language => `${question}/${language}`)));
const actualPairs = new Set(fixtures.cases.map(row => `${row.question_key}/${row.language}`));
if (actualPairs.size !== fixtures.cases.length || actualPairs.size !== expectedPairs.size || [...expectedPairs].some(pair => !actualPairs.has(pair))) throw new Error("Positive fixtures must cover every manifest question/language pair exactly once.");
const healthResponse = await fetch(new URL("/api/health", base), { signal: AbortSignal.timeout(15000) });
const health = await healthResponse.json();
if (!healthResponse.ok || !health.available) throw new Error("The live executor is not configured.");
const started = new Date().toISOString(), rows = [];
for (const fixture of fixtures.cases) {
  const spec = manifest.questions[fixture.question_key].languages[fixture.language];
  const job_json = JSON.stringify({ language: fixture.language, source: fixture.source, stdin: "", spec });
  const stamp = Math.floor(Date.now() / 1000);
  const header = Buffer.from(JSON.stringify({ alg: "EdDSA", typ: "JWT" })).toString("base64url");
  const claims = Buffer.from(JSON.stringify({ iss: "jobrun-api", aud: "jobrun-executor", sub: "00000000-0000-4000-8000-000000000001", jti: randomUUID(), iat: stamp, exp: stamp + 90, sha256: createHash("sha256").update(job_json).digest("hex") })).toString("base64url");
  const ticket = `${header}.${claims}.${sign(null, Buffer.from(`${header}.${claims}`), privateKey).toString("base64url")}`;
  let row;
  try {
    const response = await fetch(new URL("/api/execute", base), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_json, ticket }), signal: AbortSignal.timeout(65000) });
    const raw = await response.text();
    if (Buffer.byteLength(raw) > 131072) throw new Error("oversized_response");
    let result;
    try { result = JSON.parse(raw); } catch { throw new Error("invalid_response"); }
    const ok = response.ok && result.status === "passed" && result.passed === true && result.test_count > 0 && result.test_count === result.passed_count;
    row = { question: fixture.question_key, language: fixture.language, status: result.status, http_status: response.status, ok, test_count: result.test_count, passed_count: result.passed_count, runtime_ms: result.runtime_ms, ...(!ok ? { detail: result.detail, compile_output: result.compile_output, stderr: result.stderr, cases: result.cases } : {}) };
  } catch (error) {
    // Network/provider failures cannot establish whether the invocation ran.
    row = { question: fixture.question_key, language: fixture.language, status: "transport_error", ok: false, error_type: String(error?.name ?? "Error") };
  }
  rows.push(row); console.log(JSON.stringify(row));
}
const summary = { live: true, kind: "all-authored-positive-execution", executor: base, started_at: started, finished_at: new Date().toISOString(), concurrency: 1, checked: rows.length, passed: rows.filter(row => row.ok).length, failed: rows.filter(row => !row.ok).length, question_count: new Set(rows.map(row => row.question)).size, languages: [...new Set(rows.map(row => row.language))] };
if (process.argv[2]) await writeFile(process.argv[2], JSON.stringify({ summary, rows }, null, 2) + "\n", "utf8");
console.log(JSON.stringify(summary));
if (summary.failed) process.exitCode = 1;
