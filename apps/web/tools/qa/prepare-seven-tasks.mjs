// Prepare an isolated screenshot_server.py account for manual product QA.
// No browser control, database, external account, or real model is used.
//
// node tools/qa/prepare-seven-tasks.mjs --session-file <fixture-session.json>
//   --web-origin http://localhost:3212 --out <qa-scenarios.json> [--finish-today]
import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";

const args = process.argv.slice(2);
const value = (name) => {
  const index = args.indexOf(name);
  return index < 0 ? undefined : args[index + 1];
};
const sessionFile = value("--session-file");
if (!sessionFile) throw new Error("--session-file must point to screenshot_server.py's local session file");
const config = JSON.parse(readFileSync(sessionFile, "utf8"));
const loopback = (raw) => {
  const url = new URL(raw);
  assert.equal(url.protocol, "http:");
  assert.ok(["localhost", "127.0.0.1", "[::1]"].includes(url.hostname), "This helper only permits isolated local fixtures");
  return url.origin;
};
const api = loopback(config.api);
const stub = loopback(config.stub);
const web = loopback(value("--web-origin") ?? "http://localhost:3212");
assert.equal((await (await fetch(`${stub}/health`)).json()).stub, true, "Supabase must be the local fixture");
const health = await (await fetch(`${api}/health`)).json();
assert.equal(health.store, "memory", "Database-backed servers must never be seeded by this helper");

async function call(method, path, body) {
  const response = await fetch(`${api}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${config.session.access_token}`,
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  assert.ok(response.ok, `${method} ${path}: HTTP ${response.status}`);
  return response.json();
}

async function settled(id) {
  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    const attempt = await call("GET", `/v1/practice/attempts/${id}`);
    if (attempt.status !== "evaluating" && !attempt.feedback_pending && !attempt.pending_follow_up?.question_pending) return attempt;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("The scripted fixture did not settle in 20 seconds");
}

const interviewDate = new Date(Date.now() + 10 * 86400_000).toISOString().slice(0, 10);
await call("POST", "/v1/me/goal", { job_type: "verification", interview_date: interviewDate, minutes_per_day: 30, seniority: "student", language: "he" });
const questions = await call("GET", "/v1/questions?language=he");
assert.ok(questions.length >= 60);
const companyNames = (question) => new Set([
  ...(question.reported_companies ?? []),
  ...(question.companies ?? []).map((company) => company.name),
]);
const metadata = [...questions].sort((a, b) => companyNames(b).size - companyNames(a).size)[0];
assert.ok(companyNames(metadata).size > 3, "A multi-company question is needed for compact/detail QA");

async function pendingFollowUp() {
  const attempt = await call("POST", "/v1/practice/attempts", { question_key: "example-sensor-majority", mode: "deep", language: "he" });
  await call("POST", `/v1/practice/attempts/${attempt.id}/submissions`, { answer: { text: "alarm = A ^ B ^ C" } });
  const result = await settled(attempt.id);
  assert.ok(result.pending_follow_up, "A weak scripted answer should leave a follow-up for manual QA");
  return result;
}

// Leave one unanswered follow-up for real pointer/keyboard validation.
const pending = await pendingFollowUp();
// Independently verify the skip contract on another synthetic attempt.
const skipped = await pendingFollowUp();
const progressBefore = await call("GET", "/v1/me/progress?language=he");
const skipPath = `/v1/practice/attempts/${skipped.id}/follow-ups/${skipped.pending_follow_up.turn}/skip`;
const skippedView = await call("POST", skipPath);
assert.equal(skippedView.pending_follow_up, null);
const repeated = await call("POST", skipPath);
assert.equal(repeated.pending_follow_up, null);
const progressAfter = await call("GET", "/v1/me/progress?language=he");
assert.equal(progressAfter.overview.xp_total, progressBefore.overview.xp_total, "Skipping must not grant XP");
assert.equal(progressAfter.overview.answered, progressBefore.overview.answered, "Skipping must not count as an answer");

let program = await call("GET", "/v1/me/program?language=he");
if (args.includes("--finish-today")) {
  const result = await call("POST", "/__harness/finish-today");
  program = result.program;
  assert.equal(program.next, null);
  assert.ok(program.ahead, "The ten-day fixture should leave future work available");
}
const readiness = await call("GET", "/v1/me/readiness?language=he");
assert.ok(readiness.next_questions.length > 0);
const result = {
  fixture_only: true,
  catalog_count: questions.length,
  metadata_question: { key: metadata.key, companies: companyNames(metadata).size, topics: metadata.topics },
  skip_contract: { idempotent: true, no_extra_xp: true, no_extra_answer: true },
  today_remaining: program.today.length,
  ahead_available: Boolean(program.ahead),
  readiness: { covered: readiness.coverage, ready_to_judge: readiness.ready_to_judge, suggestions: readiness.next_questions.map((q) => q.key) },
  links: {
    library: `${web}/?view=library`,
    metadata: `${web}/?question=${encodeURIComponent(metadata.key)}`,
    pending_follow_up: `${web}/?attempt=${pending.id}`,
    skipped_follow_up: `${web}/?attempt=${skipped.id}`,
    today_and_ahead: `${web}/`,
    readiness: `${web}/?view=progress`,
    written_interview: `${web}/?view=interview`,
  },
};
if (value("--out")) writeFileSync(value("--out"), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
