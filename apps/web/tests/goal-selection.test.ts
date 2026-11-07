import { test } from "node:test";
import assert from "node:assert/strict";
import type { Goal } from "../src/lib/practice-api";
import { goalJobTypes, goalProgramKey, goalRoleLabel } from "../src/lib/goal-selection";
import { personalAreaEntryUrl, readWorkspaceRoute } from "../src/lib/workspace-route";

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

const origin = "https://jobrun.example";

test("entry and reload start at home even from a previously focused question, interview, game or shop", () => {
  for (const path of ["/", "/?view=library&nav=1", "/?view=library&question=q&source=retry", "/?view=history&attempt=a#feedback",
    "/?view=interview&interview=i&duration=30", "/?view=fundamentals&quick=quick-hw-01", "/games?duel=d", "/games/shop#my-character"]) {
    const url = new URL(path, origin);
    assert.equal(personalAreaEntryUrl(url, "", "navigate", false), "/");
    assert.equal(personalAreaEntryUrl(url, origin + "/games", "reload", false), "/");
    assert.equal(personalAreaEntryUrl(url, origin + "/games", "navigate", true), "/");
  }
  assert.equal(personalAreaEntryUrl(new URL("/?attempt=a&utm_source=course#feedback", origin), "https://external.example/", "navigate", false), "/?utm_source=course");
});

test("focused links and in-session back navigation preserve real work", () => {
  assert.equal(readWorkspaceRoute("?view=library&question=q&source=retry").route.question, "q");
  assert.equal(readWorkspaceRoute("?view=library&question=q&source=retry").route.source, "retry");
  assert.equal(readWorkspaceRoute("?view=history&attempt=a").route.attempt, "a");
  assert.equal(readWorkspaceRoute("?view=interview&interview=i").route.interview, "i");
  assert.equal(readWorkspaceRoute("?view=progress&attempt=a").route.view, "learn");
  assert.equal(readWorkspaceRoute("?view=library").route.view, "library");
});

test("site links, browser history and shared duel invites keep their destination", () => {
  for (const view of ["learn", "library", "interview"]) {
    const url = new URL(`/?view=${view}&nav=1`, origin);
    assert.equal(personalAreaEntryUrl(url, origin + "/games/shop", "navigate", false), null);
    const destination = readWorkspaceRoute(url.search);
    assert.equal(destination.route.view, view);
    assert.equal(new URLSearchParams(destination.search).has("nav"), false);
  }
  for (const path of ["/games", "/games/shop", "/?view=library&question=q"]) {
    assert.equal(personalAreaEntryUrl(new URL(path, origin), origin + "/", "navigate", false), null);
    assert.equal(personalAreaEntryUrl(new URL(path, origin), "", "back_forward", false), null);
  }
  assert.equal(personalAreaEntryUrl(new URL("/duel/ABC123", origin), "", "navigate", true), null);
});
