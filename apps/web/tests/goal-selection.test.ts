import { test } from "node:test";
import assert from "node:assert/strict";
import type { Goal } from "../src/lib/practice-api";
import { goalJobTypes, goalProgramKey, goalRoleLabel } from "../src/lib/goal-selection";
import { readWorkspaceRoute } from "../src/lib/workspace-route";

const goal = (updates: Partial<Goal> = {}): Goal => ({ job_type: "verification", job_type_label: "Verification", interview_date: null, days_to_interview: null, minutes_per_day: 37, seniority: "junior", complete: true, ...updates });

test("legacy goals and plural role selections retain their full personal plan selection", () => {
  assert.deepEqual(goalJobTypes(goal()), ["verification"]);
  const multi = goal({ job_types: ["verification", "software", "verification"], job_type_labels: ["Verification", "Software"] });
  assert.deepEqual(goalJobTypes(multi), ["verification", "software"]);
  assert.equal(goalRoleLabel(multi, "en"), "Verification · Software");
  assert.deepEqual(goalJobTypes(goal({ job_types: [] })), []);
});

test("exploration cannot accidentally resurrect a legacy target role", () => {
  const explore = goal({ learning_mode: "explore", job_types: ["verification"] });
  assert.deepEqual(goalJobTypes(explore), []);
  assert.equal(goalRoleLabel(explore, "he"), "למידה ללא יעד מוגדר");
});

test("every plan-affecting field refreshes the program, while reordered role chips do not", () => {
  const original = goal({ job_types: ["verification", "software"] });
  assert.equal(goalProgramKey(original), goalProgramKey({ ...original, job_types: ["software", "verification"] }));
  for (const update of [{ job_types: ["verification", "fpga"] }, { learning_mode: "explore" as const }, { minutes_per_day: 38 }, { seniority: "mid" as const }, { interview_date: "2026-12-10" }]) assert.notEqual(goalProgramKey(original), goalProgramKey({ ...original, ...update }));
});

test("fresh workspace visits always start in Personal Area, including saved category URLs", () => {
  for (const search of ["", "?view=library", "?view=history", "?view=interview&duration=30", "?view=progress"]) {
    const result = readWorkspaceRoute(search, true);
    assert.equal(result.route.view, "learn");
    assert.equal(new URLSearchParams(result.search).has("view"), false);
  }
});

test("focused links and in-session back navigation preserve real work", () => {
  assert.equal(readWorkspaceRoute("?view=library&question=q&source=retry", true).route.question, "q");
  assert.equal(readWorkspaceRoute("?view=library&question=q&source=retry", true).route.source, "retry");
  assert.equal(readWorkspaceRoute("?view=history&attempt=a", true).route.attempt, "a");
  assert.deepEqual(readWorkspaceRoute("?view=interview&interview=i", true).route.interview, "i");
  assert.equal(readWorkspaceRoute("?view=progress&attempt=a", true).route.view, "learn");
  assert.equal(readWorkspaceRoute("?view=library").route.view, "library");
});
