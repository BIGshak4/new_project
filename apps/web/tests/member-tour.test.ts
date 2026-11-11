import test from "node:test";
import assert from "node:assert/strict";
import {
  advanceMemberTour, completeMemberTourTask, initialMemberTourProgress, memberTaskKey,
  memberTourKey, memberTourStepReady, memberTourSteps, moveMemberTour, parseMemberTourProgress,
  type MemberTourProgress,
} from "../src/lib/member-tour";

test("live account curriculum visits every current category and keeps prose and code on a software question", () => {
  assert.deepEqual(memberTourSteps.map(step => step.id), [
    "goal", "dashboard", "library", "explanation", "code", "circuit", "fundamentals", "games", "friends", "shop", "interview", "helper",
  ]);
  assert.equal(memberTourSteps.find(step => step.id === "explanation")?.questionSubject, "software");
  assert.equal(memberTourSteps.find(step => step.id === "code")?.questionSubject, "software");
  assert.equal(memberTourSteps.find(step => step.id === "circuit")?.questionSubject, "hardware");
  assert.deepEqual(new Set(memberTourSteps.map(step => step.href)), new Set([
    "/?view=learn&nav=1", "/?view=library&nav=1", "/?view=fundamentals&nav=1", "/games", "/games/shop", "/?view=interview&nav=1",
  ]));
  for (const step of memberTourSteps) {
    assert.equal(new Set(step.tasks.map(task => task.id)).size, step.tasks.length, step.id);
    assert.ok(step.tasks.some(task => !task.optional), `${step.id} has a completion task`);
    for (const copy of [step.chapter, step.title, step.body, ...step.tasks.map(task => task.text)]) assert.ok(copy.he.trim() && copy.en.trim());
  }
});

test("saving a goal, AI feedback, checking a game answer and using the helper require successful app events", () => {
  assert.deepEqual(memberTourSteps.flatMap(step => step.tasks.filter(task => task.event).map(task => [step.id, task.event])), [
    ["goal", "goal-saved"], ["code", "feedback-ready"], ["games", "game-practice-answered"], ["helper", "helper-used"],
  ]);
  const code = memberTourSteps.find(step => step.id === "code")!;
  let progress = moveMemberTour(initialMemberTourProgress("learner"), code.id);
  for (const task of code.tasks.filter(task => !task.event)) progress = completeMemberTourTask(progress, code.id, task.id);
  assert.equal(memberTourStepReady(code, progress), false);
  assert.equal(advanceMemberTour(progress), progress, "A submit click alone does not bypass the feedback milestone");
  progress = completeMemberTourTask(progress, code.id, "feedback");
  assert.equal(memberTourStepReady(code, progress), true);
  assert.equal(advanceMemberTour(progress).stepId, "circuit");
});

test("tour progress is account scoped and rejects stale sample-tour checkpoints and corrupted values", () => {
  const empty = initialMemberTourProgress("one");
  const valid = { ...empty, status: "active", updatedAt: 123 };
  for (const raw of [null, "", "{", "null", "[]", "1", " ".repeat(30_001),
    JSON.stringify({ ...valid, version: 2 }), JSON.stringify({ ...valid, userId: "two" }),
    JSON.stringify({ ...valid, status: "unexpected" }),
    JSON.stringify({ version: 2, kind: "member", completed: ["goal"], stepId: "code" }),
  ]) assert.deepEqual(parseMemberTourProgress(raw, "one"), empty);
  assert.notEqual(memberTourKey("one"), memberTourKey("two"));
  assert.deepEqual(parseMemberTourProgress(JSON.stringify(valid), "one"), valid);
});

test("checkpoint parsing strips private answers, invalid task names and duplicate data", () => {
  const parsed = parseMemberTourProgress(JSON.stringify({
    ...initialMemberTourProgress("learner"), stepId: "retired-station", updatedAt: -1,
    completedTasks: ["goal:saved", "goal:saved", "code:retired", "guess", null, 42],
    skippedSteps: ["interview", "interview", "retired-station", null],
    explanation: "private answer", code: "private code", friendCode: "private code",
  }), "learner");
  assert.equal(parsed.stepId, "goal");
  assert.equal(parsed.updatedAt, 0);
  assert.deepEqual(parsed.completedTasks, ["goal:saved"]);
  assert.deepEqual(parsed.skippedSteps, ["interview"]);
  assert.deepEqual(Object.keys(parsed).sort(), Object.keys(initialMemberTourProgress("learner")).sort());
  assert.ok(!JSON.stringify(parsed).includes("private"));
});

test("optional activities never force a purchase, friend request, microphone permission or timed interview", () => {
  for (const id of ["friends", "shop", "interview", "explanation"]) {
    const step = memberTourSteps.find(item => item.id === id)!;
    let progress = moveMemberTour(initialMemberTourProgress("learner"), id);
    for (const task of step.tasks.filter(task => !task.optional)) progress = completeMemberTourTask(progress, id, task.id);
    assert.equal(memberTourStepReady(step, progress), true, id);
    const next = advanceMemberTour(progress);
    assert.notEqual(next.stepId, id, id);
    assert.equal(next.skippedSteps.includes(id), false);
  }
  const required = memberTourSteps.flatMap(step => step.tasks.filter(task => !task.optional));
  assert.ok(required.every(task => !/shop-save|game-invite|interview-start|dictation|friends-input/.test(task.selector ?? "")));
});

test("an unavailable service can be skipped and revisited without erasing earlier real work", () => {
  let progress = moveMemberTour(initialMemberTourProgress("learner"), "code");
  progress = completeMemberTourTask(progress, "code", "open");
  const skipped = advanceMemberTour(progress, true);
  assert.equal(skipped.stepId, "circuit");
  assert.deepEqual(skipped.skippedSteps, ["code"]);
  assert.ok(skipped.completedTasks.includes(memberTaskKey("code", "open")));
  let revisited = moveMemberTour(skipped, "code");
  for (const task of memberTourSteps.find(step => step.id === "code")!.tasks) revisited = completeMemberTourTask(revisited, "code", task.id);
  revisited = advanceMemberTour(revisited);
  assert.equal(revisited.skippedSteps.includes("code"), false);
  assert.ok(skipped.skippedSteps.includes("code"), "Updates preserve the original snapshot");
});

test("finishing all stops round-trips safely and duplicate app events do not add progress", () => {
  let progress: MemberTourProgress = initialMemberTourProgress("learner");
  for (const step of memberTourSteps) {
    progress = moveMemberTour(progress, step.id);
    for (const task of step.tasks) progress = completeMemberTourTask(progress, step.id, task.id);
    const repeated = completeMemberTourTask(progress, step.id, step.tasks[0].id);
    assert.equal(repeated, progress);
    assert.equal(completeMemberTourTask(progress, step.id, "unknown"), progress);
    assert.equal(moveMemberTour(progress, "unknown"), progress);
    progress = advanceMemberTour(progress);
    assert.deepEqual(parseMemberTourProgress(JSON.stringify(progress), "learner"), progress);
  }
  assert.equal(progress.status, "completed");
  assert.deepEqual(progress.skippedSteps, []);
  assert.equal(progress.completedTasks.length, memberTourSteps.reduce((sum, step) => sum + step.tasks.length, 0));
});
