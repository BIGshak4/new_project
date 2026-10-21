import { test } from "node:test";
import assert from "node:assert/strict";
import { renderToStaticMarkup } from "react-dom/server";
import { createElement } from "react";
import { quickQuestions, quickTopics, filterQuickQuestions } from "../src/lib/fundamentals";
import { QuickPractice, QuickDiagramView } from "../src/components/quick-practice";
import { hasHumanReviewedSolution, solutionReviewLabel } from "../src/lib/solution-review";
import type { QuickProgressApi } from "../src/lib/fundamentals-progress";

const api: QuickProgressApi = {
  fundamentalsProgress: async () => ({ completed: [] }),
  completeFundamental: async () => { throw new Error("Unexpected SSR mutation"); },
  resetFundamental: async () => { throw new Error("Unexpected SSR mutation"); },
};

test("120 concise cards follow the requested 50/35/15 mix and every code answer fits five lines", () => {
  assert.equal(quickQuestions.length, 120);
  assert.equal(new Set(quickQuestions.map(q => q.id)).size, 120);
  assert.equal(quickQuestions.filter(q => q.id.startsWith("quick-hw-")).length, 60);
  assert.equal(quickQuestions.filter(q => q.topic === "reasoning").length, 42);
  assert.equal(quickQuestions.filter(q => ["python", "algorithms"].includes(q.topic)).length, 18);
  for (let start = 0; start < 120; start += 20) {
    const group = quickQuestions.slice(start, start + 20);
    assert.equal(group.filter(q => q.id.startsWith("quick-hw-")).length, 10);
    assert.equal(group.filter(q => q.topic === "reasoning").length, 7);
    assert.equal(group.filter(q => ["python", "algorithms"].includes(q.topic)).length, 3);
  }
  for (const topic of quickTopics) assert.ok(quickQuestions.some(q => q.topic === topic.id));
  for (const question of quickQuestions) {
    for (const lang of ["he", "en"] as const) {
      assert.ok(question.title[lang].trim());
      assert.ok(question.prompt[lang].trim().split(/\s+/).length <= 50, question.id);
      assert.ok(question.answer[lang].trim().split(/\s+/).length <= 65, question.id);
      assert.ok(question.takeaway[lang].trim());
    }
    if (question.code) assert.ok(question.code.text.split("\n").length <= 5, question.id);
    assert.equal("solution_review" in question, false);
  }
});

test("topic and bilingual search compose; empty results remain empty", () => {
  assert.equal(filterQuickQuestions("python", "", "he").length, 6);
  const q = quickQuestions[0];
  assert.ok(filterQuickQuestions(q.topic, q.title.en, "en").includes(q));
  assert.ok(filterQuickQuestions(q.topic, q.title.he, "he").includes(q));
  assert.equal(filterQuickQuestions("python", "no-matching-card-123456", "he").length, 0);
});

test("initial quick practice loads owned history before showing potentially repeated questions", () => {
  for (const lang of ["he", "en"] as const) {
    const html = renderToStaticMarkup(createElement(QuickPractice, { lang, api, userId: "alice" }));
    assert.ok(html.includes('aria-expanded="false"'));
    assert.equal(html.includes('id="quick-answer"'), false);
    assert.equal(html.includes("quick-diagram"), false);
    assert.equal(html.includes("quick-takeaway"), false);
    assert.ok(html.includes(lang === "he" ? "טוענים את השאלות שכבר סיימתם" : "Loading your finished questions"));
    assert.ok(html.includes(lang === "he" ? "טרם נבדקו בידי אנשים" : "awaiting human review"));
  }
});

test("all authored diagrams render with labelled arrows and one initial state where relevant", () => {
  const cards = quickQuestions.filter(q => q.diagram);
  assert.ok(cards.length >= 18);
  for (const q of cards) for (const lang of ["he", "en"] as const) {
    const diagram = q.diagram!;
    const html = renderToStaticMarkup(createElement(QuickDiagramView, { diagram, lang }));
    assert.ok(html.includes('role="img"'));
    assert.ok(html.includes("marker-end="));
    if (diagram.kind === "fsm") {
      assert.ok(diagram.states.includes(diagram.initial));
      for (const edge of diagram.transitions) {
        assert.ok(diagram.states.includes(edge.from)); assert.ok(diagram.states.includes(edge.to));
      }
    }
  }
});

test("human solution review never follows trial or assessment flags", () => {
  assert.equal(hasHumanReviewedSolution({}), false);
  assert.equal(hasHumanReviewedSolution({ solution_review: { status: "pending_review", reviewed_on: null } }), false);
  assert.equal(hasHumanReviewedSolution({ solution_review: { status: "human_reviewed", reviewed_on: "2026-10-21" } }), true);
  assert.equal(solutionReviewLabel({}, "en"), "Solution review pending");
});
