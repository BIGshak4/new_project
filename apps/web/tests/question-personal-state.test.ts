import assert from "node:assert/strict";
import { afterEach, before, mock, test } from "node:test";
import type { QuestionSummary } from "../src/lib/practice-api";
import type { Entry } from "../src/lib/practice-ui";
import { matchesLibraryStatuses } from "../src/lib/library-filters";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "test-publishable-key";
let state: typeof import("../src/lib/question-personal-state");
let db: (typeof import("../src/lib/supabase"))["supabase"];
before(async () => {
  state = await import("../src/lib/question-personal-state");
  db = (await import("../src/lib/supabase")).supabase;
});
afterEach(() => mock.restoreAll());

const primary = { id: "p", key: "prep-power-of-two-check" } as QuestionSummary;
const alias = { id: "a", key: "example-power-of-two-check" } as QuestionSummary;
const other = { id: "o", key: "other-question" } as QuestionSummary;
const entry = (question_id: string, patch: Partial<Entry> = {}): Entry => ({
  id: `entry-${question_id}`, user_id: "owner", question_id, answer: "my draft",
  self_rating: 2, bookmarked: true, completed: false, hidden: false, version: 1, ...patch,
});

test("personal state survives deduplication and searches that only match a legacy alias", () => {
  const states = state.buildQuestionStates([primary, alias, other], [
    entry(primary.id, { hidden: true }), entry(alias.id, { completed: true }),
  ]);
  assert.deepEqual(states.get(primary.id), { completed: true, hidden: true });
  assert.deepEqual(states.get(alias.id), states.get(primary.id));
  assert.deepEqual(states.get(other.id), { completed: false, hidden: false });
  assert.deepEqual(state.questionStateIds(alias, [other, primary, alias, alias]), ["a", "p"]);
  assert.equal(state.matchesQuestionStatus(states.get(alias.id)!, "visible"), false);
});

test("Done returns the owner's older and newer completions across capped pages", async () => {
  const first = { ...entry("01", { completed: true }), updated_at: "2025-10-01" };
  const last = { ...entry("03", { completed: true }), updated_at: new Date().toISOString() };
  const pages = [[first, entry("02")], [last]];
  const requests: URL[] = [];
  mock.method(globalThis, "fetch", async (input: RequestInfo | URL) => {
    const url = new URL(input instanceof Request ? input.url : String(input));
    const index = requests.length;
    requests.push(url);
    assert.equal(url.searchParams.get("user_id"), "eq.owner");
    assert.equal(url.searchParams.get("order"), "question_id.asc");
    assert.equal(url.searchParams.has("updated_at"), false);
    assert.equal(url.searchParams.get("question_id"), index === 0 ? null : "gt.02");
    return Response.json(pages[index], { headers: { "Content-Range": index === 0 ? "0-1/3" : "0-0/1" } });
  });
  const rows = await state.readQuestionEntries("owner");
  const questions = rows.map(row => ({ id: row.question_id, key: row.question_id } as QuestionSummary));
  const statuses = state.buildQuestionStates(questions, rows);
  assert.deepEqual(questions.filter(q => matchesLibraryStatuses(statuses.get(q.id)!, ["done"])).map(q => q.id), ["01", "03"]);
  assert.equal(requests.length, 2);
});

test("hidden questions are separate from done/not done without losing completion", () => {
  for (const completed of [false, true]) {
    assert.equal(state.matchesQuestionStatus({ completed, hidden: true }, "hidden"), true);
    for (const filter of ["visible", "done", "not_done"] as const) {
      assert.equal(state.matchesQuestionStatus({ completed, hidden: true }, filter), false);
    }
    assert.equal(state.matchesQuestionStatus({ completed, hidden: false }, "visible"), true);
    assert.equal(state.matchesQuestionStatus({ completed, hidden: false }, "done"), completed);
    assert.equal(state.matchesQuestionStatus({ completed, hidden: false }, "not_done"), !completed);
  }
});

test("hide patches only visibility for all family IDs and keeps returned notes/completion", async () => {
  const rows = [entry("a", { completed: true, hidden: true }), entry("p", { hidden: true })];
  const rpc = mock.method(db, "rpc", async () => ({ data: rows, error: null }));
  assert.deepEqual(await state.saveQuestionState("owner", ["p", "a", "p"], { hidden: true }), rows);
  assert.deepEqual(rpc.mock.calls[0].arguments, ["jr_set_question_state", {
    p_question_ids: ["a", "p"], p_completed: null, p_hidden: true,
  }]);
});

test("explicit reset writes false, and failed or foreign-account responses never look saved", async () => {
  const rpc = mock.method(db, "rpc", async (): Promise<{ data: Entry[] | null; error: { message: string } | null }> => ({ data: [entry("p")], error: null }));
  await state.saveQuestionState("owner", ["p"], { completed: false });
  assert.equal((rpc.mock.calls[0].arguments[1] as { p_completed: boolean }).p_completed, false);
  rpc.mock.mockImplementation(async () => ({ data: [entry("p", { user_id: "other" })], error: null }));
  await assert.rejects(state.saveQuestionState("owner", ["p"], { hidden: true }));
  rpc.mock.mockImplementation(async () => ({ data: [], error: null }));
  await assert.rejects(state.saveQuestionState("owner", ["p"], { hidden: true }));
  rpc.mock.mockImplementation(async () => ({ data: null, error: { message: "denied" } }));
  await assert.rejects(state.saveQuestionState("owner", ["p"], { hidden: true }));
});
