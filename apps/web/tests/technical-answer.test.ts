import { test } from "node:test";
import assert from "node:assert/strict";
import {
  answerLanguages,
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

test("only the last same-fence answer is code; an earlier flawed example remains explanation", () => {
  const explanation = "Earlier flawed example:\n\n```python\ndef f(x):\n return 0\n```";
  assert.deepEqual(parseTechnicalAnswer(`${explanation}\n\n\`\`\`python\ndef f(x):\n return x\n\`\`\``), {
    explanation,
    language: "python",
    code: "def f(x):\n return x",
  });
});

test("the final exact fence selects the last recognized answer across languages and fence lengths", () => {
  for (const language of answerLanguages) for (const fence of ["```", "````", "``````"]) {
    const explanation = `הסבר לפני הדוגמאות.\n\n\`\`\`python\nreturn 0\n\`\`\`\n\n${fence}${language}\nfirst version\n${fence}`;
    const value = `${explanation}\n\n${fence}${language}\nfinal version\n${fence}`;
    assert.deepEqual(parseTechnicalAnswer(value), { explanation, language, code: "final version" });
    assert.deepEqual(parseTechnicalAnswer(value + "\n"), { explanation, language, code: "final version" });
  }
});

test("formatter round-trips embedded fence lines and literal openings in every supported language", () => {
  const explanation = "Earlier code stays in reasoning:\n\n```cpp\nreturn 0;\n```\n";
  const code = 'literal with `inline` backticks\n\n```python\nthis is part of the code\n```\n\n`````javascript\nmore literal source\n`````\n\r\n';
  for (const language of answerLanguages) {
    assert.deepEqual(parseTechnicalAnswer(formatTechnicalAnswer(explanation, code, language)), { explanation, language, code });
    assert.deepEqual(parseTechnicalAnswer(formatTechnicalAnswer("", code, language)), { explanation: "", language, code });
  }
});

test("a final unknown block, mismatched fence or trailing prose never consumes an earlier recognized block", () => {
  const earlier = "```python\nreturn 0\n```";
  for (const value of [
    `${earlier}\n\n\`\`\`unknown\nnew code\n\`\`\``,
    `${earlier}\n\n\`\`\`\`python\nnew code\n\`\`\``,
    `${earlier}\n\n\`\`\`python\nnew code\n\`\`\`\ntrailing reasoning`,
    `${earlier}\n\n\`\`\`python\nnew code\n\`\`\`\n\n`,
  ]) assert.deepEqual(parseTechnicalAnswer(value), { explanation: value, code: "", language: undefined });
});
