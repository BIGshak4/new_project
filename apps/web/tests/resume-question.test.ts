import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { resumeCandidates } from "../src/lib/resume-question";
import { readWorkspaceRoute } from "../src/lib/workspace-route";
import type { PracticeApi, Progress, QuestionSummary } from "../src/lib/practice-api";
import type { QuestionVisit } from "../src/lib/question-visit-store";
import type { Entry } from "../src/lib/practice-ui";

const require = createRequire(import.meta.url);
require.extensions[".css"] = module => { module.exports = {}; };
process.env.NEXT_PUBLIC_SUPABASE_URL = "http://localhost:8792";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "resume-test-key";

const opened = (questionKey: string, visitedAt: number, attemptId: string | null = null): QuestionVisit =>
  ({ kind: "practice", questionKey, attemptId, visitedAt });
const attempt = (id: string, question_key: string, time: number, submitted = false): Progress["recent"][number] =>
  ({ id, question_key, started_at: new Date(time).toISOString(), submitted_at: submitted ? new Date(time + 1).toISOString() : null,
    band: null, mode: "deep", language: "he", hints_used: 0, reference_revealed: false });

test("last visit takes precedence over an attempt start and a preview resumes its pending attempt", () => {
  const result = resumeCandidates([opened("old", 10, "a"), opened("old", 40), opened("new-preview", 20)],
    [attempt("b", "other", 30), attempt("a", "old", 5)]);
  assert.deepEqual(result.map(v => [v.questionKey, v.attemptId]), [["old", "a"], ["other", "b"], ["new-preview", null]]);
  assert.equal(result[0].visitedAt, 40);
});

test("a newer submitted attempt does not resurrect an old abandoned attempt for the same question", () => {
  assert.deepEqual(resumeCandidates([opened("x", 1)], [attempt("old", "x", 1), attempt("new", "x", 15, true)]), []);
  assert.deepEqual(resumeCandidates([], [attempt("elsewhere", "other", 20)]), [opened("other", 20, "elsewhere")]);
});

test("home verifies live attempts, skips completed or hidden records, and opens the actual remaining short card", async () => {
  const { findContinuation } = await import("../src/components/resume-question");
  const { quickQuestions } = await import("../src/lib/fundamentals");
  const quick = quickQuestions[0];
  const records = [opened("submitted", 50, "attempt-id"), opened("hidden", 40), opened("removed", 30),
    { ...opened(quick.id, 20), kind: "quick" as const }];
  const api = {
    getAttempt: async () => ({ question: { key: "submitted" }, submission: { key: "accepted" } }),
    fundamentalsProgress: async (userId: string) => { assert.equal(userId, "owner"); return { completed: [] }; },
  } as unknown as PracticeApi;
  const inputs = { api, userId: "owner", lang: "en" as const, recent: [],
    questions: ["submitted", "hidden"].map(key => ({ key, id: key, title: key } as QuestionSummary)),
    entries: [{ question_id: "hidden", hidden: true } as Entry] };
  const result = await findContinuation(inputs, records, () => false);
  assert.equal(result?.visit.questionKey, quick.id);
  assert.equal(result?.title, quick.title.en);
  const completedApi = { ...api, fundamentalsProgress: async () => ({ completed: [{ question_key: quick.id,
    content_revision: "0".repeat(64), completed_at: "2026-11-07T10:00:00Z" }] }) };
  assert.equal(await findContinuation({ ...inputs, api: completedApi }, records, () => false), null);
});

test("only a valid short question ID can open a card when continuing practice", () => {
  assert.equal(readWorkspaceRoute("?view=fundamentals&quick=quick-hw-01").route.quick, "quick-hw-01");
  assert.equal(readWorkspaceRoute("?view=fundamentals&quick=quick-hw-01").route.view, "fundamentals");
  assert.equal(readWorkspaceRoute("?view=fundamentals&quick=unknown").route.quick, undefined);
  assert.equal(readWorkspaceRoute("?view=library&quick=quick-hw-01").route.quick, undefined);
});
