import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { QuestionPrompt } from "../src/components/question-prompt";

const bank = JSON.parse(readFileSync(new URL("../../../backend/seeds/questions/preparation_bank.json", import.meta.url), "utf8")) as Array<{
  key: string; translations: Record<"en" | "he", { prompt: string }>;
}>;
const tunnel = bank.find(q => q.key === "prep-bridge-torch-twelve-hours")!;

test("the tunnel question precedes its separately expandable canoe variation in both languages", () => {
  for (const lang of ["he", "en"] as const) {
    const html = renderToStaticMarkup(createElement(QuestionPrompt, { text: tunnel.translations[lang].prompt, questionKey: tunnel.key, lang }));
    const beforeDetails = html.split("<details>", 1)[0];
    assert.match(beforeDetails, lang === "he" ? /מנהרה/ : /dark tunnel/);
    assert.doesNotMatch(beforeDetails, lang === "he" ? /קאנו/ : /canoe/i);
    assert.match(html, lang === "he" ? /<summary>ניסוחים נוספים \(וריאציות\)<\/summary>/ : /<summary>Alternative wordings \(variations\)<\/summary>/);
    assert.match(html.slice(html.lastIndexOf("<summary>")), lang === "he" ? /קאנו/ : /canoe/i);
    assert.doesNotMatch(html, /<details[^>]*\bopen\b/);
  }
});

test("short questions preserve their compact heading and skip blank or duplicate alternatives", () => {
  const text = "What does a rising edge mean?";
  const base = { text, lang: "en" as const, heading: "h3" as const };
  const render = (additionalWordings: string[]) => renderToStaticMarkup(createElement(QuestionPrompt, { ...base, additionalWordings }));
  const compact = render(["  ", text]);
  assert.match(compact, /^<h3[^>]*>/);
  assert.doesNotMatch(compact, /details|summary|question-disclosures/);
  const alternative = "Explain a zero-to-one transition.";
  const expanded = render([alternative, alternative]);
  assert.equal(expanded.split("zero-to-one transition").length - 1, 1);
  assert.equal(expanded.split("<details>").length - 1, 1);
});

test("a saved English question can keep English prose and show Hebrew disclosure controls", () => {
  const html = renderToStaticMarkup(createElement(QuestionPrompt, {
    text: tunnel.translations.en.prompt, questionKey: tunnel.key, lang: "he", contentLang: "en",
  }));
  assert.match(html, /<p dir="ltr">/);
  assert.match(html, /class="question-disclosures" lang="he" dir="rtl"/);
  assert.match(html, /<summary>ניסוחים נוספים \(וריאציות\)<\/summary>/);
});

test("assumptions that define a single-line timed question stay visible with its task", () => {
  const html = renderToStaticMarkup(createElement(QuestionPrompt, {
    text: "Assume equal gate delay and ignore wiring. Compute the longest path.",
    questionKey: "quick-hw-106-v2", lang: "en", heading: "h1",
  }));
  assert.match(html, /Assume equal gate delay and ignore wiring/);
  assert.match(html, /Compute the longest path/);
  assert.doesNotMatch(html, /details|summary/);
});

test("given code and choices appear once with the task while optional sections are closed", () => {
  const html = renderToStaticMarkup(createElement(QuestionPrompt, {
    text: "Trace this function.", lang: "en", additionalWordings: ["Try it with a different input."],
  }, createElement("pre", null, "return bits[1]"),
  createElement("ol", null, createElement("li", null, "Choice A"), createElement("li", null, "Choice B"))));
  const [visible, optional] = html.split("<details>");
  assert.match(visible, /Trace this function\.[\s\S]*<pre>return bits\[1\]<\/pre>[\s\S]*Choice A[\s\S]*Choice B/);
  assert.match(optional, /Try it with a different input/);
  assert.doesNotMatch(optional, /return bits|Choice A|Choice B/);
});
