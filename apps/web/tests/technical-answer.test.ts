import { test } from "node:test";
import assert from "node:assert/strict";
import {
  formatTechnicalAnswer,
  parseTechnicalAnswer,
} from "../src/lib/technical-answer";

test("Hebrew reasoning and exact LTR code round-trip through saved answer text", () => {
  for (const language of ["c", "verilog", "vhdl", "text"] as const) {
    const explanation = "נבדוק את מקרה הקצה n=0.\nוגם שעון ואיפוס.";
    const code =
      "module test;\n\t// עברית inside code\n  wire [3:0] a;\nendmodule\n";
    const text = formatTechnicalAnswer(explanation, code, language);
    assert.deepEqual(parseTechnicalAnswer(text), {
      explanation,
      code,
      language,
    });
  }
});
test("legacy prose and unfamiliar fences are never discarded", () => {
  for (const answer of [
    "plain old draft\n",
    "```unknown\nsaved code\n```",
    "before\n```c\ncode\n```\nafter",
  ]) {
    assert.deepEqual(parseTechnicalAnswer(answer), {
      explanation: answer,
      code: "",
      language: undefined,
    });
  }
});
test("technical content with backticks, blank lines and no prose remains recoverable", () => {
  const code = "  table\n```\nA B | Y\n0 1 | 1\n";
  assert.deepEqual(
    parseTechnicalAnswer(formatTechnicalAnswer("", code, "text")),
    { explanation: "", code, language: "text" },
  );
  assert.equal(formatTechnicalAnswer("draft", "", "c"), "draft");
});
