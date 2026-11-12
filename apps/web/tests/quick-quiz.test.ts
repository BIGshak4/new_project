import assert from "node:assert/strict";
import { test } from "node:test";
import { createRequire } from "node:module";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { quickQuestions, quickTopics, type QuickQuestion, type QuickTopic } from "../src/lib/fundamentals";
import { readQuickQuizRun, selectQuickQuiz } from "../src/lib/quick-quiz";

process.env.NEXT_PUBLIC_SUPABASE_URL = "http://localhost:8792";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "quiz-render-test-key";
const require = createRequire(import.meta.url);
require.extensions[".css"] = module => { module.exports = {}; };

test("every topic and a selected combination sample exactly ten distinct eligible questions", () => {
  const before = JSON.stringify(quickQuestions);
  for (const topics of [...quickTopics.map(topic => [topic.id]), ["gates", "bits"] as QuickTopic[], quickTopics.map(topic => topic.id)]) {
    for (let seed = 1; seed <= 25; seed++) {
      const run = selectQuickQuiz(topics, seed)!;
      assert.equal(run.questionIds.length, 10);
      assert.equal(new Set(run.questionIds).size, 10);
      assert.ok(run.questionIds.every(id => topics.includes(quickQuestions.find(question => question.id === id)!.topic)));
    }
  }
  assert.equal(JSON.stringify(quickQuestions), before);
});

test("the full topic pool participates, and repeat rendering can reuse fixed IDs", () => {
  const topics = quickTopics.map(topic => topic.id);
  assert.deepEqual(selectQuickQuiz(topics, 72), selectQuickQuiz(topics, 72));
  assert.notDeepEqual(selectQuickQuiz(topics, 72)!.questionIds, selectQuickQuiz(topics, 73)!.questionIds);
  const allSeen = new Set(Array.from({ length: 1500 }, (_, seed) => selectQuickQuiz(topics, seed)!.questionIds).flat());
  assert.equal(allSeen.size, 700);
});

test("empty or undersized pools cannot produce a partial or duplicate quiz", () => {
  assert.equal(selectQuickQuiz([], 12), null);
  const small = quickQuestions.filter(question => question.topic === "bits").slice(0, 9);
  assert.equal(selectQuickQuiz(["bits"], 12, small), null);
  assert.equal(selectQuickQuiz(["bits"], 12, [...small, ...small] as QuickQuestion[]), null);
});

test("restored quiz history is owned, complete and constrained to its chosen topics", () => {
  const selection = selectQuickQuiz(["bits"], 14)!;
  const run = { ...selection, id: "quiz-run" };
  assert.deepEqual(readQuickQuizRun({ owner: "alice", run }, "alice"), run);
  assert.equal(readQuickQuizRun({ owner: "alice", run }, "bob"), null);
  for (const invalid of [null, {}, { ...run, questionIds: run.questionIds.slice(1) }, { ...run, topics: [] },
    { ...run, topics: ["gates"] }, { ...run, questionIds: Array(10).fill(run.questionIds[0]) },
    { ...run, questionIds: [...run.questionIds.slice(1), "missing-question"] }]) {
    assert.equal(readQuickQuizRun({ owner: "alice", run: invalid }, "alice"), null);
  }
});

test("quiz page renders all ten prompts with closed solutions and real report controls in either language", async () => {
  const { QuickQuiz } = await import("../src/components/quick-quiz");
  const run = { ...selectQuickQuiz(["gates", "python"], 24)!, id: "render-run" };
  for (const lang of ["he", "en"] as const) {
    const html = renderToStaticMarkup(createElement(QuickQuiz, { run, lang, onBack: () => {}, onNew: () => {} }));
    assert.equal((html.match(/data-quiz-question=/g) ?? []).length, 10);
    assert.equal((html.match(/aria-expanded="false" aria-controls="quiz-/g) ?? []).length, 10);
    assert.equal(html.includes('class="quick-answer"'), false);
    assert.equal(html.includes('class="quick-takeaway"'), false);
    assert.equal((html.match(new RegExp(lang === "he" ? "דיווח בעיה" : "Report a problem", "g")) ?? []).length, 10);
    assert.ok(html.includes(lang === "he" ? "בוחן חדש" : "New quiz"));
    assert.ok(html.includes(lang === "he" ? "ללא ציון" : "ungraded"));
    for (const id of run.questionIds) assert.ok(html.includes(`data-quiz-question="${id}"`));
  }
});
