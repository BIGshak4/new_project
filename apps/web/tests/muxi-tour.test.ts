import test from "node:test";
import assert from "node:assert/strict";
import { lockBodyScroll } from "../src/lib/body-scroll-lock";
import { checkpoint, initialTourProgress, parseTourProgress, stationReady, tourKey, tourSteps, type TourKind, type TourProgress } from "../src/lib/muxi-tour";

test("every stop in both experiences teaches through a distinct user action", () => {
  for (const kind of ["preview", "member"] as const) {
    const steps = tourSteps(kind);
    const ids = steps.map(s => s.id);
    assert.equal(new Set(ids).size, ids.length);
    for (const step of steps) {
      for (const text of [step.title, step.body, step.chapter, step.task]) {
        assert.ok(text.he.trim() && text.en.trim());
      }
      assert.ok(step.actions.length);
      assert.equal(stationReady(step, ["panel-seen", "next-clicked", ...steps.filter(s => s !== step).flatMap(s => s.actions)]), false, step.id);
      assert.equal(stationReady(step, step.actions), true);
    }
  }
});

test("a visitor can try the current library, hardware, software, evaluation, quiz and interview without a goal", () => {
  assert.deepEqual(tourSteps("preview").map(step => step.exercise), ["library", "circuit", "code", "feedback", "quiz", "interview"]);
  assert.deepEqual(tourSteps("member").map(step => step.exercise), ["goal", "library", "circuit", "code", "feedback", "quiz", "interview", "community", "helper"]);
  assert.deepEqual(tourSteps("member")[0].actions, ["goal-saved"]);
});

test("corrupt checkpoints, obsolete simulations and checkpoints for another audience restart safely", () => {
  for (const kind of ["preview", "member"] as const) {
    const initial = initialTourProgress(kind);
    for (const value of [null, "", "{", "null", "[]", "1", " ".repeat(20001),
      JSON.stringify({ ...initial, version: 1, kind: "short", completed: ["goal"] }),
      JSON.stringify(initialTourProgress(kind === "member" ? "preview" : "member")),
      JSON.stringify({ ...initial, status: "bad" })]) {
      assert.deepEqual(parseTourProgress(value, kind), initial);
    }
    assert.deepEqual(initialTourProgress(kind).completed, []);
  }
});

test("an account checkpoint stores only known stations, normalizes duplicates and strips answer content", () => {
  const parsed = parseTourProgress(JSON.stringify({
    ...initialTourProgress("member"), offered: true, stepId: "old", completed: ["goal", "goal", "removed", 1],
    skipped: ["goal", "quiz", "quiz", null], updatedAt: "unknown", answer: "private words", code: "private code",
  }), "member");
  assert.deepEqual(parsed.completed, ["goal"]);
  assert.deepEqual(parsed.skipped, ["quiz"]);
  assert.equal(parsed.stepId, "library");
  assert.equal(parsed.updatedAt, 0);
  assert.deepEqual(Object.keys(parsed).sort(), Object.keys(initialTourProgress("member")).sort());
  assert.ok(!JSON.stringify(parsed).includes("private"));
  assert.notEqual(tourKey(), tourKey("visitor"));
  assert.notEqual(tourKey("one"), tourKey("two"));
  assert.match(tourKey("one"), /v2/);
});

test("completing a previously skipped station updates just that station", () => {
  const steps = tourSteps("member");
  const original = initialTourProgress("member");
  const skipped = checkpoint(original, steps[0], "skipped", steps[1]);
  const completed = checkpoint(skipped, steps[0], "completed", steps[1]);
  const revisited = checkpoint(completed, steps[0], "skipped", steps[1]);
  assert.deepEqual(original, initialTourProgress("member"));
  assert.deepEqual(skipped.skipped, ["goal"]);
  assert.deepEqual(completed.completed, ["goal"]);
  assert.deepEqual(completed.skipped, []);
  assert.deepEqual(revisited.completed, ["goal"]);
  assert.deepEqual(revisited.skipped, []);
  assert.equal(completed.stepId, "library");
});

test("both routes can be paused, resumed and completed without restoring exercise data", () => {
  for (const kind of ["preview", "member"] as TourKind[]) {
    const steps = tourSteps(kind);
    let p: TourProgress = initialTourProgress(kind);
    for (const [index, step] of steps.entries()) {
      p = checkpoint(p, step, index % 2 ? "skipped" : "completed", steps[index + 1]);
      assert.deepEqual(parseTourProgress(JSON.stringify(p), kind), p);
    }
    assert.equal(p.status, "completed");
    assert.equal(p.completed.length + p.skipped.length, steps.length);
  }
});

const fakeDocument = (overflow = "") => ({ body: { style: { overflow } } }) as unknown as Document;

test("nested tour and expanded-circuit scroll locks release correctly in either cleanup order", () => {
  for (const original of ["", "auto", "scroll", "hidden"]) {
    for (const parentFirst of [true, false]) {
      const document = fakeDocument(original);
      const releaseTour = lockBodyScroll(document);
      assert.equal(document.body.style.overflow, "hidden");
      const releaseCircuit = lockBodyScroll(document);
      const [first, last] = parentFirst ? [releaseTour, releaseCircuit] : [releaseCircuit, releaseTour];
      first();
      assert.equal(document.body.style.overflow, "hidden", "A still-open nested surface must retain the lock");
      last();
      assert.equal(document.body.style.overflow, original, "The last cleanup must restore the original page overflow");
    }
  }
});

test("scroll-lock cleanup is idempotent and cannot release another active surface's lock", () => {
  const document = fakeDocument("auto");
  const releaseTour = lockBodyScroll(document);
  const releaseCircuit = lockBodyScroll(document);
  releaseTour();
  releaseTour();
  releaseTour();
  assert.equal(document.body.style.overflow, "hidden");
  releaseCircuit();
  assert.equal(document.body.style.overflow, "auto");
  releaseCircuit();
  assert.equal(document.body.style.overflow, "auto");
  document.body.style.overflow = "scroll";
  const releaseNextTour = lockBodyScroll(document);
  releaseTour();
  assert.equal(document.body.style.overflow, "hidden", "Old cleanup callbacks must not unlock a later tour");
  releaseNextTour();
  assert.equal(document.body.style.overflow, "scroll", "A new lock cycle must capture its own current overflow");
});

test("scroll locks are isolated per document rather than leaking across independent windows", () => {
  const one = fakeDocument("auto"), two = fakeDocument("scroll");
  const releaseOne = lockBodyScroll(one), releaseTwo = lockBodyScroll(two);
  releaseOne();
  assert.equal(one.body.style.overflow, "auto");
  assert.equal(two.body.style.overflow, "hidden");
  releaseTwo();
  assert.equal(two.body.style.overflow, "scroll");
});
