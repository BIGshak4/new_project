import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { StudyText } from "../src/components/question-materials";
import { solutionMarkdown } from "../src/lib/solution-markdown";

test("Hebrew prose isolates an LTR expression while retaining every character in order", () => {
  const html = renderToStaticMarkup(createElement(StudyText, { text: "הביטוי הוא x!=0 && (x & (x-1))==0. התוצאות: false,true,false,true,true." }));
  assert.match(html, /<bdi dir="ltr">x!=0 &amp;&amp; \(x &amp; \(x-1\)\)==0<\/bdi>/);
  assert.match(html, /<bdi dir="ltr">false,true,false,true,true<\/bdi>/);
  assert.match(html, /הביטוי הוא/);
});

test("solution labels become sections while fenced source code remains verbatim", () => {
  const source = "**הנחה:** קלט שלם.\n\n**הפתרון:**\n\n```python\n# **not a heading**\nreturn n > 0 and (n & (n - 1)) == 0\n```\n\n**למה זה עובד?** הסבר.";
  const normalized = solutionMarkdown(source);
  assert.match(normalized, /^### הנחה\n\nקלט שלם\./);
  assert.match(normalized, /# \*\*not a heading\*\*/);
  assert.match(normalized, /### למה זה עובד\?/);
  const html = renderToStaticMarkup(createElement(StudyText, { text: source, solution: true }));
  assert.match(html, /<h3>הנחה<\/h3>/);
  assert.match(html, /<pre class="code-block" dir="ltr"><code class="language-python" dir="ltr">/);
  assert.match(html, /return n &gt; 0 and \(n &amp; \(n - 1\)\) == 0/);
});

test("mixed technical headings at every level isolate the whole expression", () => {
  for (let level = 1; level <= 6; level++) {
    const html = renderToStaticMarkup(createElement(StudyText, { text: `${"#".repeat(level)} בדיקה של A XOR B בשער` }));
    assert.match(html, /<bdi dir="ltr">A XOR B<\/bdi>/);
    assert.match(html, new RegExp(`<h${level}>`));
  }
});

test("table columns follow their own header language instead of the surrounding prose", () => {
  const text = "הטבלה הטכנית מופיעה כאן.\n\n| `A` | **B** | C | alarm |\n|---|---|---|---|\n| 0 | 1 | 0 | 1 |\n\nAn English introduction.\n\n| יום | עבודה |\n|---|---|\n| היום | Practice |";
  const html = renderToStaticMarkup(createElement(StudyText, { text }));
  assert.deepEqual([...html.matchAll(/<table dir="(ltr|rtl)">/g)].map((match) => match[1]), ["ltr", "rtl"]);
  assert.match(html, /<code dir="ltr">A<\/code>/);
  assert.ok(html.indexOf("A</code>") < html.indexOf("alarm</bdi>"));
});

test("table direction skips neutral digits and punctuation and keeps numeric tables LTR", () => {
  for (const [text, direction] of [
    ["| (1) קלט | פלט |\n|---|---|\n| A | B |", "rtl"],
    ["| 0 | 1 |\n|---|---|\n| 1 | 0 |", "ltr"],
    ["| מצב | next |\n|---|---|\n| S0 | S1 |", "rtl"],
  ] as const) {
    const html = renderToStaticMarkup(createElement(StudyText, { text }));
    assert.match(html, new RegExp(`<table dir="${direction}">`));
  }
});

test("formatting retains the existing protections against author HTML, image requests and unsafe links", () => {
  const html = renderToStaticMarkup(createElement(StudyText, { text: '<script>alert(1)</script>\n\n![image](https://example.com/private.png)\n\n[link](javascript:alert(1))' }));
  assert.doesNotMatch(html, /<script|<img|javascript:|href=/);
});

test("all 67 bilingual catalog prompts and references render with the production study-text component", () => {
  const questions = ["example_bank", "preparation_bank"].flatMap(name =>
    JSON.parse(readFileSync(new URL(`../../../backend/seeds/questions/${name}.json`, import.meta.url), "utf8")));
  assert.equal(questions.length, 67);
  for (const question of questions) {
    for (const language of ["he", "en"]) {
      const text = question.translations[language];
      for (const field of ["prompt", "reference_solution"]) {
        const html = renderToStaticMarkup(createElement(StudyText, {
          text: text[field], solution: field === "reference_solution",
        }));
        assert.ok(html.length > 50, `${question.key}/${language}/${field}`);
        assert.doesNotMatch(html, /<script|<img/);
      }
    }
  }
});
