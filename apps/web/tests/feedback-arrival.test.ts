import assert from "node:assert/strict";
import { test } from "node:test";
import type { Attempt, Submission } from "../src/lib/practice-api";
import { FeedbackArrivalTracker } from "../src/lib/feedback-arrival";

function submission(overrides: Partial<Submission> = {}): Submission {
  return { revision: 1, status: "done", assessed_by: "model", ...overrides } as Submission;
}
function attempt(main: Submission | null, overrides: Partial<Attempt> = {}): Attempt {
  return { id: "a", status: "done", submission: main, follow_ups: [], ...overrides } as Attempt;
}

test("grade-first responses wait until all feedback words have arrived", () => {
  const tracker = new FeedbackArrivalTracker();
  assert.equal(tracker.observe(attempt(null, { status: "in_progress" })), null);
  assert.equal(tracker.observe(attempt(submission({ status: "evaluating" }), { status: "evaluating" })), null);
  assert.equal(tracker.observe(attempt(submission({ feedback_pending: true }), { feedback_pending: true })), null);
  assert.equal(tracker.observe(attempt(submission(), { feedback_pending: true })), null);
  assert.equal(tracker.observe(attempt(submission({ feedback_pending: true }))), null);
  assert.deepEqual(tracker.observe(attempt(submission())), { attemptId: "a", revision: 1 });
});

test("an immediately completed submit also produces an arrival", () => {
  const tracker = new FeedbackArrivalTracker();
  tracker.observe(attempt(null, { status: "in_progress" }));
  assert.deepEqual(tracker.observe(attempt(submission())), { attemptId: "a", revision: 1 });
});

test("historical feedback loaded already complete does not jump", () => {
  const tracker = new FeedbackArrivalTracker();
  assert.equal(tracker.observe(attempt(submission())), null);
  assert.equal(tracker.observe(attempt(submission(), { reference: "opened reference" })), null);
});

test("reopening an in-flight attempt still jumps when its feedback finishes", () => {
  const tracker = new FeedbackArrivalTracker();
  tracker.observe(attempt(submission({ feedback_pending: true }), { feedback_pending: true }));
  assert.deepEqual(tracker.observe(attempt(submission())), { attemptId: "a", revision: 1 });
});

test("a cancelled render frame can retry, but repeated polls after delivery do not jump", () => {
  const tracker = new FeedbackArrivalTracker();
  tracker.observe(attempt(null));
  const ready = attempt(submission());
  const first = tracker.observe(ready)!;
  // React Strict Mode can cancel an effect's frame before it focuses the report.
  assert.deepEqual(tracker.observe({ ...ready }), first);
  tracker.acknowledge(first);
  assert.equal(tracker.observe({ ...ready }), null);
  assert.equal(tracker.observe({ ...ready, reference: "reference" }), null);
});

test("a new attempt suppresses old history and does not inherit another attempt's delivery", () => {
  const tracker = new FeedbackArrivalTracker();
  tracker.observe(attempt(null));
  const oldArrival = tracker.observe(attempt(submission()))!;
  tracker.observe(attempt(null, { id: "b" }));
  tracker.acknowledge(oldArrival);
  assert.deepEqual(tracker.observe(attempt(submission(), { id: "b" })), { attemptId: "b", revision: 1 });
  assert.equal(tracker.observe(attempt(submission(), { id: "historic" })), null);
});

test("failed reports do not scroll; a successful retry on the same revision does", () => {
  const tracker = new FeedbackArrivalTracker();
  tracker.observe(attempt(submission({ status: "evaluating" }), { status: "evaluating" }));
  assert.equal(tracker.observe(attempt(submission({ status: "failed" }), { status: "failed" })), null);
  assert.equal(tracker.observe(attempt(submission({ status: "evaluating" }), { status: "evaluating" })), null);
  assert.deepEqual(tracker.observe(attempt(submission())), { attemptId: "a", revision: 1 });
});

test("demo and unassessed answers are not presented as newly generated feedback", () => {
  for (const assessed_by of ["demo", "unassessed"] as const) {
    const tracker = new FeedbackArrivalTracker();
    tracker.observe(attempt(null));
    assert.equal(tracker.observe(attempt(submission({ assessed_by }))), null);
  }
});

test("a follow-up arrival selects its new revision, never the previous main feedback", () => {
  const tracker = new FeedbackArrivalTracker();
  tracker.observe(attempt(submission()));
  const followUp = { turn: 1, submission: submission({ turn: 1, revision: 2, status: "evaluating" }) };
  const evaluating = attempt(submission(), { status: "evaluating", follow_ups: [followUp] as Attempt["follow_ups"] });
  assert.equal(tracker.observe(evaluating), null);
  assert.equal(tracker.observe(attempt(submission())), null); // stale response
  const ready = { ...evaluating, status: "done", follow_ups: [{ ...followUp, submission: submission({ turn: 1, revision: 2 }) }] } as Attempt;
  const arrival = tracker.observe(ready)!;
  assert.deepEqual(arrival, { attemptId: "a", revision: 2 });
  tracker.acknowledge(arrival);
  assert.equal(tracker.observe({ ...ready, pending_follow_up: null }), null);
});

test("leaving the attempt resets the baseline when the reader returns to its report", () => {
  const tracker = new FeedbackArrivalTracker();
  tracker.observe(attempt(null));
  tracker.reset();
  assert.equal(tracker.observe(attempt(submission())), null);
});
