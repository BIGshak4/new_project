import { test } from "node:test";
import assert from "node:assert/strict";
import { renderToStaticMarkup } from "react-dom/server";
import { createElement } from "react";
import { quickQuestions, quickTopics, filterQuickQuestions } from "../src/lib/fundamentals";
import { QuickPractice, QuickDiagramView } from "../src/components/quick-practice";
import { hasHumanReviewedSolution, solutionReviewLabel } from "../src/lib/solution-review";

test("sixty original concise cards cover every topic and every code answer fits five lines", () => {
  assert.equal(quickQuestions.length, 60);
  assert.equal(new Set(quickQuestions.map(q => q.id)).size, 60);
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
  assert.equal(filterQuickQuestions("python", "", "he").length, 10);
  const q = quickQuestions[0];
  assert.ok(filterQuickQuestions(q.topic, q.title.en, "en").includes(q));
  assert.ok(filterQuickQuestions(q.topic, q.title.he, "he").includes(q));
  assert.equal(filterQuickQuestions("python", "no-matching-card-123456", "he").length, 0);
});

test("initial quick practice asks a question without rendering its answer, code or diagram", () => {
  for (const lang of ["he", "en"] as const) {
    const html = renderToStaticMarkup(createElement(QuickPractice, { lang }));
    assert.ok(html.includes('aria-expanded="false"'));
    assert.equal(html.includes('id="quick-answer"'), false);
    assert.equal(html.includes("quick-diagram"), false);
    assert.equal(html.includes("quick-takeaway"), false);
    assert.ok(html.includes(lang === "he" ? "טרם נבדקו בידי אנשים" : "awaiting human review"));
  }
});

test("all ten authored diagrams render with labelled arrows and one initial state where relevant", () => {
  const cards = quickQuestions.filter(q => q.diagram);
  assert.ok(cards.length >= 10);
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
