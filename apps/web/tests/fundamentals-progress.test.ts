import { test } from "node:test";
import assert from "node:assert/strict";
import { quickQuestions } from "../src/lib/fundamentals";
import { confirmQuickCompletion, filterQuickHistory, quickCompletionState, quickRevision, readQuickProgress } from "../src/lib/fundamentals-progress";
import type { FundamentalCompletion } from "../src/lib/practice-api";

const first = quickQuestions[0], second = quickQuestions[1];
const completion: FundamentalCompletion = { question_key: first.id, content_revision: quickRevision(first.id), completed_at: "2026-10-21T12:00:00Z" };

test("saved per-question history excludes completed cards by default and makes them revisitable", () => {
  const records = readQuickProgress({ completed: [completion] });
  assert.equal(quickCompletionState(first, records), "completed");
  assert.equal(quickCompletionState(second, records), "unanswered");
  assert.equal(filterQuickHistory(quickQuestions, records, "unanswered").some(q => q.id === first.id), false);
  assert.deepEqual(filterQuickHistory(quickQuestions, records, "completed").map(q => q.id), [first.id]);
  assert.equal(filterQuickHistory(quickQuestions, records, "all").length, 400);
  const afterReload = readQuickProgress(JSON.parse(JSON.stringify({ completed: [completion] })));
  assert.equal(filterQuickHistory(quickQuestions, afterReload, "unanswered").length, 399);
});

test("an updated question keeps its history label and does not silently repeat", () => {
  const records = readQuickProgress({ completed: [{ ...completion, content_revision: "0".repeat(64) }] });
  assert.equal(quickCompletionState(first, records), "updated");
  assert.equal(filterQuickHistory([first], records, "unanswered").length, 0);
  assert.equal(filterQuickHistory([first], records, "completed").length, 1);
  assert.equal(confirmQuickCompletion(completion, first.id).content_revision, quickRevision(first.id));
  assert.throws(() => confirmQuickCompletion({ ...completion, content_revision: "0".repeat(64) }, first.id));
});

test("a failed or malformed history response cannot masquerade as an empty completed list", () => {
  for (const input of [null, {}, { completed: null }, { completed: [{}] }, { completed: [completion, completion] },
    { completed: [{ ...completion, completed_at: "invalid" }] }, { completed: [{ ...completion, content_revision: "bad" }] }]) {
    assert.throws(() => readQuickProgress(input as never));
  }
  assert.deepEqual(readQuickProgress({ completed: [] }), {});
});

test("completion acknowledgements must belong to the question and its current content", () => {
  assert.deepEqual(confirmQuickCompletion(completion, first.id), completion);
  assert.throws(() => confirmQuickCompletion(completion, second.id));
  assert.throws(() => confirmQuickCompletion({ ...completion, completed_at: "bad" }, first.id));
});
