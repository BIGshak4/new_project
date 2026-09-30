import { test } from "node:test";
import assert from "node:assert/strict";
import type { QuestionSummary } from "../src/lib/practice-api";
import { companyNames, matchesCompany, matchesQuestion, normalizeSearch, questionCategory } from "../src/lib/question-discovery";

const question = { title: "Multiplexer", key: "prep-mux", subject: "digital_fundamentals", category: "hardware",
  topics: ["logic_gates"], reported_companies: ["Intel", "NVIDIA"], companies: [] } as unknown as QuestionSummary;

test("both searches find company names across Hebrew, case, whitespace and diacritics", () => {
  for (const input of ["Intel", "intel", "INTEL", " אינטל ", "אִינְטֶל", "NVIDIA", "אנבידיה", "נווידיה"]) {
    assert.equal(matchesCompany(question, input), true, input);
    assert.equal(matchesQuestion(question, input), true, input);
  }
  assert.equal(matchesCompany(question, "Google"), false);
  assert.equal(matchesQuestion(question, "גוגל"), false);
  assert.equal(matchesQuestion(question, "Intel חומרה"), true);
  assert.equal(matchesQuestion(question, "Intel תוכנה"), false);
});

test("live sightings and source reports merge without inventing or duplicating reports", () => {
  const q = { companies: [{ name: "אינטל", slug: "intel", count: 3 }, { name: "New Company", slug: "new-company", count: 1 }], reported_companies: ["INTEL", "Intel"] };
  assert.deepEqual(companyNames(q), ["Intel", "New Company"]);
  assert.equal(matchesCompany(q, "NEW company"), true);
  assert.equal(matchesQuestion({ ...question, ...q }, "אינטל"), true);
  assert.deepEqual(companyNames({}), []);
});

test("spacing and punctuation aliases preserve distinct corporate reports", () => {
  const q = { reported_companies: ["Check Point", "Mellanox"] };
  for (const input of ["CHECKPOINT", "צ׳ק פוינט", "צ'ק פוינט", "צקפוינט", "מלאנוקס"]) assert.equal(matchesCompany(q, input), true);
  assert.equal(matchesCompany(q, "NVIDIA"), false); // acquisition does not fabricate a report
});

test("metadata fallback supports older cached questions and empty searches", () => {
  assert.equal(questionCategory({ subject: "fsms" }), "hardware");
  assert.equal(questionCategory({ subject: "reasoning" }), "logic");
  assert.equal(questionCategory({ subject: "relevant_programming" }), "software");
  assert.equal(questionCategory({ subject: "unknown" }), "general");
  assert.equal(matchesQuestion(question, "  "), true);
  assert.equal(matchesCompany(question, "  "), true);
  assert.equal(normalizeSearch("Logic_Gates"), "logic gates");
  assert.equal(matchesQuestion(question, "logic gates"), true);
});
