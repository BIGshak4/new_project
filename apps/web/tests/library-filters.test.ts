import { test } from "node:test";
import assert from "node:assert/strict";
import type { QuestionSummary } from "../src/lib/practice-api";
import { emptyLibraryFilters, matchesLibraryFilters, matchesLibraryStatuses } from "../src/lib/library-filters";
const question = (update: Partial<QuestionSummary> = {}) => ({ key: "mux", title: "Build a MUX", subject: "digital_logic", job_types: ["verification", "digital_design"], reported_companies: ["Apple"], ...update } as QuestionSummary);
const state = { completed: false, hidden: false };
test("fresh defaults include every question irrespective of goal, completion or hidden state", () => {
  for (const personal of [state, { completed: true, hidden: false }, { completed: false, hidden: true }]) assert.equal(matchesLibraryFilters(question(), personal, emptyLibraryFilters()), true);
  const first = emptyLibraryFilters(); first.jobs.push("software"); assert.deepEqual(emptyLibraryFilters().jobs, []);
});
test("Apple and NVIDIA are a union and do not include a third company", () => {
  const filters = { ...emptyLibraryFilters(), companies: ["Apple", "NVIDIA"] };
  assert.equal(matchesLibraryFilters(question(), state, filters), true);
  assert.equal(matchesLibraryFilters(question({ reported_companies: ["אנבידיה"] }), state, filters), true);
  assert.equal(matchesLibraryFilters(question({ reported_companies: ["Intel"] }), state, filters), false);
});
test("multiple subjects, roles and disciplines intersect the selected company union", () => {
  const filters = { ...emptyLibraryFilters(), categories: ["hardware", "software"], subjects: ["digital_logic", "programming"], jobs: ["verification", "software"], companies: ["Apple", "NVIDIA"] };
  assert.equal(matchesLibraryFilters(question(), state, filters), true);
  assert.equal(matchesLibraryFilters(question({ subject: "programming", job_types: ["software"] }), state, filters), true);
  assert.equal(matchesLibraryFilters(question({ job_types: ["embedded"] }), state, filters), false);
  assert.equal(matchesLibraryFilters(question({ subject: "reasoning" }), state, filters), false);
  assert.equal(matchesLibraryFilters(question({ reported_companies: ["Intel"] }), state, filters), false);
});
test("status choices combine, with hidden questions explicitly distinguishable", () => {
  assert.equal(matchesLibraryStatuses(state, ["done", "not_done"]), true);
  assert.equal(matchesLibraryStatuses({ completed: true, hidden: false }, ["done", "not_done"]), true);
  assert.equal(matchesLibraryStatuses({ completed: true, hidden: true }, ["done", "not_done"]), false);
  assert.equal(matchesLibraryStatuses({ completed: true, hidden: true }, ["done", "hidden"]), true);
});
test("text search still narrows selected choices and empty results stay empty", () => {
  assert.equal(matchesLibraryFilters(question(), state, { ...emptyLibraryFilters(), query: "mux", companies: ["Apple"] }), true);
  assert.equal(matchesLibraryFilters(question(), state, { ...emptyLibraryFilters(), query: "counter" }), false);
});
