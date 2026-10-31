import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { BidiText } from "../src/components/bidi-text";
import { QuestionTitle } from "../src/components/question-title";

test("the Hebrew library title keeps its RTL paragraph when C++ is the first word", () => {
  const text = "C++ ניהול משאבים והריסה וירטואלית ב־Destructor";
  const html = renderToStaticMarkup(createElement(QuestionTitle, {
    lang: "he", children: createElement("button", { type: "button", className: "library-question-open" },
      createElement(BidiText, null, text)),
  }));
  assert.match(html, /^<h3 dir="rtl"><button type="button" class="library-question-open">/);
  assert.match(html, /<bdi dir="ltr">C\+\+<\/bdi>/);
  assert.match(html, /ניהול משאבים והריסה וירטואלית/);
  assert.match(html, /<bdi dir="ltr">Destructor<\/bdi>/);
  assert.match(html, /<\/button><\/h3>$/);
});

test("all question heading levels follow the UI language even for an entirely English title", () => {
  for (const as of ["h1", "h2", "h3", "h4"] as const) {
    for (const lang of ["he", "en"] as const) {
      const html = renderToStaticMarkup(createElement(QuestionTitle, {
        as, lang, className: "question-heading",
        children: createElement(BidiText, null, "C++ resource management"),
      }));
      assert.match(html, new RegExp(`^<${as} class="question-heading" dir="${lang === "he" ? "rtl" : "ltr"}">`));
      assert.match(html, /<bdi dir="ltr">C\+\+ resource management<\/bdi>/);
    }
  }
});

test("library, history, practice, next-up and circuit reference use the shared heading boundary", () => {
  for (const path of ["app/page.tsx", "components/practice-session.tsx", "components/evaluation-panel.tsx", "components/circuit-editor.tsx"]) {
    const source = readFileSync(new URL(`../src/${path}`, import.meta.url), "utf8");
    assert.match(source, /<QuestionTitle[^>]*lang=\{lang\}/, path);
    assert.doesNotMatch(source, /<h[1-4][^>]*dir=\{textDirection\([^\n]*\.title/, path);
  }
});
