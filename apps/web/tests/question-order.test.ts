import { test } from "node:test";
import assert from "node:assert/strict";
import { shuffleQuestions } from "../src/lib/question-order";
import { filterQuickQuestions, quickQuestions } from "../src/lib/fundamentals";
import { filterQuickHistory, quickRevision } from "../src/lib/fundamentals-progress";
import { uniqueLibraryQuestions } from "../src/lib/question-families";
import type { QuestionSummary } from "../src/lib/practice-api";

test("a shuffle is a fresh permutation without mutating catalog records", () => {
  const input = Object.freeze(Array.from({ length: 101 }, (_, i) => Object.freeze({ key: `question-${i}` })));
  const shuffled = shuffleQuestions(input, 123456, q => q.key);
  assert.equal(shuffled.length, input.length);
  assert.deepEqual(new Set(shuffled), new Set(input));
  assert.notDeepEqual(shuffled, input);
  assert.deepEqual(input.map(q => q.key), Array.from({ length: 101 }, (_, i) => `question-${i}`));
  assert.notDeepEqual(shuffled, shuffleQuestions(input, 987654, q => q.key));
  assert.deepEqual(shuffleQuestions([], 0, String), []);
  assert.deepEqual(shuffleQuestions(["one"], 0, String), ["one"]);
});

test("the same visit ignores backend input order and language changes", () => {
  const he = quickQuestions.map(q => ({ key: q.id, title: q.title.he }));
  const en = [...quickQuestions].reverse().map(q => ({ key: q.id, title: q.title.en }));
  const keys = (items: typeof he) => shuffleQuestions(items, 71, q => q.key).map(q => q.key);
  assert.deepEqual(keys(he), keys(en));
});

test("job matching and library dedup preserve canonical IDs in the shuffled full catalog", () => {
  const keys = ["example-power-of-two-check", "prep-power-of-two-check", "prep-fifo", "prep-stock", "prep-mux"];
  const rows = keys.map(key => ({ id: `record-${key}`, key, title: key })) as QuestionSummary[];
  const ordered = shuffleQuestions(rows, 2026, q => q.key);
  const jobKeys = new Set(["prep-stock", "prep-power-of-two-check", "example-power-of-two-check"]);
  const matching = ordered.filter(q => jobKeys.has(q.key));
  const unique = uniqueLibraryQuestions(matching);
  assert.equal(unique.length, 2);
  assert.deepEqual(new Set(unique.map(q => q.key)), new Set(["prep-stock", "prep-power-of-two-check"]));
  assert.equal(unique.find(q => q.key === "prep-power-of-two-check")?.id, "record-prep-power-of-two-check");
  // Saved rows retain the original record, even if it belongs to a duplicate family.
  const saved = matching.filter(q => q.id === "record-example-power-of-two-check");
  assert.deepEqual(saved.map(q => q.key), ["example-power-of-two-check"]);
  assert.deepEqual(ordered.filter(q => jobKeys.has(q.key)), matching);
});

test("topic, search, and completed history retain the visit order and omit finished IDs after reshuffling", () => {
  const completed = quickQuestions.filter((_, i) => i % 3 === 0);
  const records = Object.fromEntries(completed.map(q => [q.id, {
    question_key: q.id, content_revision: quickRevision(q.id), completed_at: "2026-10-21T12:00:00Z",
  }]));
  for (const seed of [0, 1, 17, 999, 0xffffffff]) {
    const ordered = shuffleQuestions(quickQuestions, seed, q => q.id);
    for (const lang of ["he", "en"] as const) {
      for (const topic of ["all", "gates", "bits", "sequential", "states", "python", "algorithms", "reasoning"] as const) {
        const matching = filterQuickQuestions(topic, "", lang, ordered);
        assert.deepEqual(matching, ordered.filter(q => topic === "all" || q.topic === topic));
        const unfinished = filterQuickHistory(matching, records, "unanswered");
        assert.deepEqual(unfinished, matching.filter(q => !records[q.id]));
        assert.ok(unfinished.every(q => !completed.some(done => done.id === q.id)));
      }
      const q = ordered[20];
      assert.ok(filterQuickQuestions("all", q.title[lang], lang, ordered).includes(q));
      assert.deepEqual(filterQuickQuestions("all", "", lang, ordered), ordered);
    }
  }
});
