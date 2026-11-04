import assert from "node:assert/strict";
import test from "node:test";
import { questionSupportRequest, type QuestionActionTarget } from "../src/lib/question-action-context";
import { supportOpenRequest, supportPageContext } from "../src/lib/support-report";

test("question report context identifies short and MC questions without requiring a long-bank key", () => {
  const short = questionSupportRequest({ questionKey: "quick-hw-042", questionTitle: "בחירת כניסה", context: "quick" }, "unclear", "he");
  assert.equal(short.questionKey, "quick-hw-042");
  assert.equal(short.category, "question");
  assert.match(short.subject!, /^שאלה לא ברורה/);
  assert.match(short.description!, /שאלה קצרה/);
  const quiz = questionSupportRequest({ questionKey: "quiz-mux:17", context: "quiz", variant: 17 }, "problem", "en");
  assert.equal(quiz.questionKey, "quiz-mux:17");
  assert.match(quiz.description!, /Multiple-choice question/);
  assert.match(quiz.description!, /Variant: 17/);
});

test("support context includes a reported company but never copies answers or account/game secrets", () => {
  const target = { questionKey: "quiz-logic", questionTitle: "Logic gate", context: "quiz", variant: 0,
    answer: "private-answer", correct: "correct-secret", explanation: "solution-secret", account: "email-secret", duelId: "private-room" };
  const request = questionSupportRequest(target as QuestionActionTarget, "company", "en", "  Intel  ");
  assert.match(request.description!, /I saw this question at: Intel/);
  assert.match(request.description!, /Variant: 0/);
  for (const secret of [target.answer, target.correct, target.explanation, target.account, target.duelId]) assert.ok(!JSON.stringify(request).includes(secret));
});

test("external support shortcuts accept only bounded fields and safe question identifiers", () => {
  assert.deepEqual(supportOpenRequest({ category: "question", subject: "a".repeat(170), description: "b".repeat(6100), questionKey: "valid-key", pagePath: "/private/secret", answer: "secret" }),
    { category: "question", subject: "a".repeat(160), description: "b".repeat(6000), questionKey: "valid-key" });
  for (const questionKey of ["https://site.test/private?token=secret", "../private", "question\nprivate", "x".repeat(201), 24]) {
    assert.equal(supportOpenRequest({ questionKey }).questionKey, undefined);
  }
  assert.deepEqual(supportOpenRequest(null), {});
  assert.deepEqual(supportOpenRequest({ subject: [], description: {}, category: "admin" }), {});
});

test("game report page context discards the room ID and unrelated URL secrets", () => {
  assert.deepEqual(supportPageContext("https://site.test/games/private-room-id?token=secret#private"), { pagePath: "/games", questionKey: null });
  assert.deepEqual(supportPageContext("https://site.test/games/preview"), { pagePath: "/games/preview", questionKey: null });
});
