import { before, test } from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { PlanItem, Program, Readiness, ReadinessSkill } from "../src/lib/practice-api";
import { eligibleAhead, todayProgress } from "../src/lib/path";
import { PlanTable } from "../src/components/progress-board";
process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "readiness-test-publishable-key";
let ReadinessContent: typeof import("../src/components/readiness-card").ReadinessContent;
let WorkAheadCard: typeof import("../src/components/learn-home").WorkAheadCard;
before(async () => {
  ({ ReadinessContent } = await import("../src/components/readiness-card"));
  ({ WorkAheadCard } = await import("../src/components/learn-home"));
});

const noop = () => {};
const planItem = (overrides: Partial<PlanItem> = {}): PlanItem => ({ id: "tomorrow-first", day_index: 1, date: "2026-10-16", mode: "deep", skills: [{ key: "gates", label: "Logic gates" }], minutes: 20, reason: "Build confidence", done: false, status: "planned", ...overrides });
const program = (overrides: Partial<Program> = {}): Program => ({ plan: { items: [planItem()], minutes_per_day: 30, days_to_interview: 10, interview_date: null, generated_for: "2026-10-15" }, today: [], next: null, ahead: planItem(), done_today: 2, minutes_due_today: 0, goal_complete: true, ...overrides });
const skill = (overrides: Partial<ReadinessSkill> = {}): ReadinessSkill => ({ key: "gates", label: "Logic gates", subject: "digital", weight_share: .3, required_level: 3, level: 2, status: "assessed", gap: 1, freshness: "fresh", askable: true, ...overrides });
const readiness = (overrides: Partial<Readiness> = {}): Readiness => ({ job_type: "hardware", job_type_label: "Hardware engineer", skills: [skill()], coverage: .8, ready_to_judge: true, readiness_word: "Nearly there", readiness_score: 87.123, skills_meeting_requirement: 1, skills_with_gap: 1, skills_without_evidence: 0, next_questions: [{ key: "q1", title: "Build a decoder", skill: "gates", skill_label: "Logic gates", difficulty: 2, why: "gap", reason: "Work on the level your role needs." }], message: "A few focused answers can close the remaining gaps.", ...overrides });
const renderReadiness = (data: Readiness | null, props: Record<string, unknown> = {}) => renderToStaticMarkup(createElement(ReadinessContent, { readiness: data, lang: "en", onRetry: noop, onEditGoal: noop, onStart: noop, ...props }));

test("working ahead requires server eligibility, a completed day, a future saved item and a complete goal", () => {
  assert.equal(eligibleAhead(program())?.id, "tomorrow-first");
  assert.equal(eligibleAhead(program({ done_today: 0 }))?.id, "tomorrow-first", "a day without due items is eligible too");
  assert.equal(eligibleAhead(program({ ahead: planItem({ status: "started" }) }))?.status, "started");
  assert.equal(eligibleAhead(null), null);
  for (const changes of [{ goal_complete: false }, { next: planItem({ day_index: 0 }) }, { today: [planItem({ day_index: 0 })] }, { ahead: null }, { ahead: undefined }]) assert.equal(eligibleAhead(program(changes)), null);
  for (const changes of [{ id: null }, { day_index: 0 }, { day_index: -1 }, { done: true }, { status: "done" }, { status: "skipped" }, { status: "unknown" }]) assert.equal(eligibleAhead(program({ ahead: planItem(changes) })), null);
});

test("offering tomorrow never changes the daily budget, completed items or progress", () => {
  const state = program();
  const snapshot = JSON.stringify(state);
  assert.deepEqual(todayProgress(state), { done: 2, total: 2, fraction: 1 });
  eligibleAhead(state);
  assert.equal(JSON.stringify(state), snapshot);
  assert.deepEqual(todayProgress(state), { done: 2, total: 2, fraction: 1 });
  assert.equal(state.minutes_due_today, 0);
  assert.equal(state.plan.minutes_per_day, 30);
});

test("working ahead explicitly labels the original day, voluntary action, pending and interview states", () => {
  const render = (item: PlanItem, busy = false, starting = false, lang: "he" | "en" = "en") => renderToStaticMarkup(createElement(WorkAheadCard, { item, lang, busy, starting, onStart: noop }));
  const html = render(planItem());
  assert.match(html, /Tomorrow/);
  assert.match(html, /Start the next item early/);
  assert.match(html, /stays assigned to its original day/);
  assert.match(render(planItem({ status: "started" })), /Continue the next item/);
  assert.match(render(planItem({ mode: "simulation" })), /Open the next planned interview/);
  assert.match(render(planItem(), true, true), /disabled=""/);
  assert.match(render(planItem(), true, true), /Opening…/);
  assert.match(render(planItem(), false, false, "he"), /להתחיל את הפריט הבא מראש/);
});

test("readiness shows a readiness word and evidence, never the score or coverage percentage", () => {
  const html = renderReadiness(readiness());
  assert.match(html, /Nearly there/);
  assert.match(html, /Required level/);
  assert.match(html, /Your level/);
  assert.match(html, /1 level to build/);
  assert.match(html, /Fresh/);
  assert.match(html, /dir="ltr">3 \/ 5/);
  assert.doesNotMatch(html, /87\.123|80%|readiness_score|coverage/);
  assert.match(html, /aria-label="Practise: Build a decoder"/);
});

test("insufficient evidence hides the readiness word even if the response contains one", () => {
  const html = renderReadiness(readiness({ ready_to_judge: false, message: "Answer the questions below before judging readiness." }));
  assert.doesNotMatch(html, /Nearly there/);
  assert.match(html, /before judging readiness/);
  assert.match(html, /Build a decoder/);
});

test("skills are ordered by weight and stale, unassessed and unaskable skills are explained", () => {
  const html = renderReadiness(readiness({ skills: [skill({ key: "lower", label: "Lower weight", weight_share: .1 }), skill({ key: "expired", label: "Expired skill", weight_share: .4, freshness: "expired", gap: null, askable: false }), skill({ key: "new", label: "Unassessed skill", weight_share: .2, freshness: "none", level: null, gap: null }), skill({ key: "aging", label: "Aging skill", weight_share: .15, freshness: "aging", gap: 0 })] }));
  assert.ok(html.indexOf("Expired skill") < html.indexOf("Unassessed skill"));
  assert.ok(html.indexOf("Unassessed skill") < html.indexOf("Lower weight"));
  assert.match(html, /Previously measured level/);
  assert.match(html, /Needs a fresh check/);
  assert.match(html, /There is no question in the bank that examines this skill yet/);
  assert.match(html, /Not assessed yet/);
  assert.match(html, /Needs an answer to assess/);
  assert.match(html, /Refresh soon/);
  assert.match(html, /Meets the requirement/);
});

test("long readiness lists use a native disclosure and recommendations are capped at three", () => {
  const state = readiness();
  const html = renderReadiness(readiness({ skills: Array.from({ length: 8 }, (_, index) => skill({ key: `skill-${index}`, label: `Skill ${index}` })), next_questions: Array.from({ length: 4 }, (_, index) => ({ ...state.next_questions[0], key: `q${index}`, title: `Question ${index}` })) }));
  assert.match(html, /<details class="readiness-more"><summary>View all 8 skills/);
  assert.equal((html.match(/class="readiness-skill freshness-/g) ?? []).length, 8);
  assert.equal((html.match(/class="readiness-question"/g) ?? []).length, 3);
  assert.doesNotMatch(html, /Question 3/);
});

test("readiness covers no-goal, no-recommendation, loading, error/retry and start error states", () => {
  const noGoal = renderReadiness(readiness({ job_type: null, job_type_label: null, skills: [], next_questions: [], ready_to_judge: false, readiness_word: null }));
  assert.match(noGoal, /Choose my role/);
  assert.doesNotMatch(noGoal, /readiness-question"/);
  assert.match(renderReadiness(readiness({ next_questions: [] })), /There are no new recommended questions/);
  const loading = renderReadiness(null, { loading: true });
  assert.match(loading, /aria-busy="true"/);
  assert.match(loading, /role="status"/);
  assert.match(renderReadiness(null, { error: "Service unavailable" }), /role="alert">Service unavailable/);
  assert.match(renderReadiness(null, { error: "Service unavailable" }), /Try again/);
  const starting = renderReadiness(readiness(), { busyKey: "q1", actionError: "Please retry this question" });
  assert.match(starting, /disabled=""/);
  assert.match(starting, /Opening…/);
  assert.match(starting, /Please retry this question/);
  assert.match(renderReadiness(readiness(), { lang: "he" }), /מוכנות לתפקיד שלכם/);
});

test("mixed server rationales and skill names preserve complete LTR expressions inside Hebrew", () => {
  const reason = "כדי לבדוק X & (X - 1) == 0 ולחזק Boolean Algebra לפני הראיון";
  const expectedExpression = '<bdi dir="ltr">X &amp; (X - 1) == 0</bdi>';
  const item = planItem({ reason, skills: [{ key: "gates", label: "פישוט בעזרת XOR(A, B) ומפות" }] });
  const table = renderToStaticMarkup(createElement(PlanTable, { plan: { ...program().plan, items: [item] }, lang: "he", onEditGoal: noop }));
  assert.ok(table.includes(expectedExpression), "the plan rationale isolates the whole expression, not individual operands");
  assert.match(table, /כדי לבדוק <bdi dir="ltr">.*<\/bdi> ולחזק <bdi dir="ltr">Boolean Algebra<\/bdi> לפני הראיון/);
  assert.match(table, /פישוט בעזרת <bdi dir="ltr">XOR\(A, B\)<\/bdi> ומפות/);
  const report = readiness();
  const card = renderReadiness({ ...report, message: reason, next_questions: [{ ...report.next_questions[0], reason }] }, { lang: "he" });
  assert.equal(card.split(expectedExpression).length - 1, 2, "readiness summary and recommendation rationale both preserve the expression");
  const ahead = renderToStaticMarkup(createElement(WorkAheadCard, { item, lang: "he", busy: false, starting: false, onStart: noop }));
  assert.match(ahead, /פישוט בעזרת <bdi dir="ltr">XOR\(A, B\)<\/bdi> ומפות/);
});
