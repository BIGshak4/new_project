import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import type { QuestionSummary } from "../src/lib/practice-api";
import { questionFamily, relatedQuestionKeys, uniqueLibraryQuestions } from "../src/lib/question-families";
import { matchesQuestion } from "../src/lib/question-discovery";

const generic = { id: "original-id", key: "example-power-of-two-check", title: "Recognize a power of two", subject: "relevant_programming" } as QuestionSummary;
const manual = { id: "manual-id", key: "prep-power-of-two-check", title: "Constant-time power-of-two test", preparation_id: "PREP-023", reported_companies: ["Intel", "NVIDIA"], subject: "relevant_programming" } as QuestionSummary;

test("a duplicate keeps the manually collected question and its provenance regardless of relevance order", () => {
  for (const rows of [[generic, manual], [manual, generic]]) {
    assert.deepEqual(uniqueLibraryQuestions(rows), [manual]);
    assert.deepEqual(uniqueLibraryQuestions(rows)[0].reported_companies, ["Intel", "NVIDIA"]);
  }
});

test("a preparation number and an older generic title remain searchable under their own IDs", () => {
  const rows = [generic, manual];
  assert.deepEqual(uniqueLibraryQuestions(rows.filter(q => matchesQuestion(q, "PREP-023"))).map(q => q.id), ["manual-id"]);
  assert.deepEqual(uniqueLibraryQuestions(rows.filter(q => matchesQuestion(q, "Recognize"))).map(q => q.id), ["original-id"]);
  assert.deepEqual(rows.map(q => q.id), ["original-id", "manual-id"], "source records and saved/history IDs are untouched");
});

test("a filtered or partial API result never loses the only available version", () => {
  assert.deepEqual(uniqueLibraryQuestions([generic]), [generic]);
  assert.deepEqual(uniqueLibraryQuestions([manual]), [manual]);
  assert.deepEqual(uniqueLibraryQuestions([]), []);
});

test("useful variations with different constraints are not silently merged", () => {
  const keys = ["example-balanced-brackets", "prep-balanced-brackets-mixed-text", "example-count-set-bits", "prep-eight-bit-popcount-adders", "prep-power-of-two-check", "prep-one-active-bit-signed-int32-pattern"];
  const rows = keys.map((key, i) => ({ ...generic, key, id: String(i) }));
  assert.deepEqual(uniqueLibraryQuestions(rows), rows);
  assert.equal(questionFamily(keys[0]), keys[0]);
});

test("legacy and canonical URLs remain discoverable in both directions", () => {
  assert.deepEqual(relatedQuestionKeys(generic.key), [manual.key]);
  assert.deepEqual(relatedQuestionKeys(manual.key), [generic.key]);
  assert.deepEqual(relatedQuestionKeys("unrelated-question"), []);
});

test("the accumulated intakes yield 176 records and 174 unique questions without dropping new exercises", () => {
  const rows = ["example_bank", "preparation_bank"].flatMap(name => {
    const seed = JSON.parse(readFileSync(new URL(`../../../backend/seeds/questions/${name}.json`, import.meta.url), "utf8"));
    return seed.map((q: { key: string; assets: { preparation_id?: string } }) => ({
      key: q.key, id: q.key, preparation_id: q.assets.preparation_id,
    } as QuestionSummary));
  });
  assert.equal(rows.length, 176);
  const unique = uniqueLibraryQuestions(rows);
  assert.equal(unique.length, 174);
  for (const id of Array.from({ length: 88 }, (_, i) => `PREP-${String(i + 60).padStart(3, "0")}`)) {
    assert.equal(rows.filter(q => q.preparation_id === id).length, 1, `${id}: one canonical source record`);
    assert.equal(unique.filter(q => q.preparation_id === id).length, 1, id);
  }
  assert.equal(unique.filter(q => q.preparation_id === "PREP-023").length, 1);
  assert.ok(!unique.some(q => q.key === "example-power-of-two-check"));
  assert.ok(!unique.some(q => q.key === "example-merge-measurement-streams"));
});

test("the merge source is preferred without rewriting the example's history or company reports", () => {
  const example = { ...generic, id: "merge-example-id", key: "example-merge-measurement-streams", title: "Merge measurement streams", reported_companies: [] };
  const collected = { ...manual, id: "merge-manual-id", key: "prep-merge-two-sorted-arrays", title: "Merge two sorted arrays", preparation_id: "PREP-098", reported_companies: ["NVIDIA"] };
  for (const rows of [[example, collected], [collected, example]]) {
    assert.deepEqual(uniqueLibraryQuestions(rows), [collected]);
    assert.deepEqual(uniqueLibraryQuestions(rows.filter(q => matchesQuestion(q, "measurement"))), [example]);
    assert.deepEqual(uniqueLibraryQuestions(rows.filter(q => matchesQuestion(q, "PREP-098"))), [collected]);
  }
  assert.deepEqual(example.reported_companies, []);
  assert.deepEqual(relatedQuestionKeys(example.key), [collected.key]);
  assert.deepEqual(relatedQuestionKeys(collected.key), [example.key]);
});
