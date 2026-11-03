import test from "node:test";
import assert from "node:assert/strict";
import { initialTourProgress, tourSteps, type TourProgress } from "../src/lib/muxi-tour";
import { tourKindForSurface, tourProgressForSurface, tourStepsForSurface } from "../src/app/tour/policy";

test("the public tour restricts every requested kind to short while authenticated tours keep both", () => {
  for (const kind of ["short", "full"] as const) {
    assert.equal(tourKindForSurface(kind, true), "short");
    assert.deepEqual(tourStepsForSurface(kind, true).map(step => step.id), tourSteps("short").map(step => step.id));
    assert.equal(tourKindForSurface(kind, false), kind);
    assert.equal(tourStepsForSurface(kind, false), tourSteps(kind));
  }
  assert.doesNotMatch(tourStepsForSurface("full", true).find(step => step.id === "theme")!.body.he, /שני הסיורים/);
});

test("an older public full checkpoint resumes safely without full-only stations", () => {
  const old: TourProgress = { ...initialTourProgress(), offered: true, stepId: "truth", completed: ["goal", "search", "truth", "photo"], skipped: ["topics", "clock"], updatedAt: 123 };
  const next = tourProgressForSurface(old, true);
  assert.equal(next.kind, "short");
  assert.equal(next.stepId, "code");
  assert.deepEqual(next.completed, ["goal", "search"]);
  assert.deepEqual(next.skipped, ["topics"]);
  assert.equal(next.updatedAt, 123);
  assert.equal(next.status, "paused");
  assert.equal(tourProgressForSurface(old, false), old);
  assert.equal(old.kind, "full", "Normalizing a visitor checkpoint must not mutate the source");
});

test("a valid short checkpoint retains its station and completed work", () => {
  const progress: TourProgress = { ...initialTourProgress(), kind: "short", stepId: "hint", completed: ["goal", "search"], skipped: ["simulate"], status: "paused" };
  assert.deepEqual(tourProgressForSurface(progress, true), progress);
  assert.equal(tourProgressForSurface(initialTourProgress(), true).kind, "short");
});
