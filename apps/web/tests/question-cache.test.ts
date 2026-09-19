import { test } from "node:test";
import assert from "node:assert/strict";
import {
  readQuestionCache,
  writeQuestionCache,
} from "../src/lib/question-cache";
import type { QuestionSummary } from "../src/lib/practice-api";

test("catalog cache isolates users/languages, expires and excludes hidden answer fields", () => {
  const values = new Map<string, string>();
  Object.defineProperty(globalThis, "sessionStorage", {
    configurable: true,
    value: {
      getItem: (k: string) => values.get(k) ?? null,
      setItem: (k: string, v: string) => values.set(k, v),
    },
  });
  const question = {
    id: "1",
    key: "q",
    title: "Question",
    subject: "fsms",
    format: "open",
    difficulty: 3,
    estimated_minutes: 10,
    practice_modes: ["deep"],
    language: "he",
    languages: ["he"],
    status: "published",
    hint_count: 3,
    has_reference: true,
    has_check: false,
    requirements: "SECRET",
    reference_solution: "SECRET",
    hints: ["SECRET"],
  };
  writeQuestionCache("alice", "he", [question as QuestionSummary]);
  assert.equal(readQuestionCache("alice", "he")?.[0].title, "Question");
  assert.equal(readQuestionCache("bob", "he"), null);
  assert.equal(readQuestionCache("alice", "en"), null);
  const [key, raw] = [...values.entries()][0];
  assert.equal(raw.includes("SECRET"), false);
  values.set(
    key,
    JSON.stringify({
      ...JSON.parse(raw),
      savedAt: Date.now() - 13 * 60 * 60 * 1000,
    }),
  );
  assert.equal(readQuestionCache("alice", "he"), null);
  values.set(key, "broken JSON");
  assert.equal(readQuestionCache("alice", "he"), null);
  delete (globalThis as { sessionStorage?: Storage }).sessionStorage;
});

test("unavailable browser storage does not prevent live use", () => {
  assert.equal(readQuestionCache("alice", "he"), null);
  assert.doesNotThrow(() => writeQuestionCache("alice", "he", []));
});
