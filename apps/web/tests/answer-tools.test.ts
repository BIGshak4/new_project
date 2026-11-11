import { test } from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { AnswerEditor } from "../src/components/answer-editor";
import { formatTechnicalAnswer } from "../src/lib/technical-answer";
import { emptyVisual, makePart, type VisualAnswer as Visual } from "../src/lib/circuit";

// This suite renders markup only; it never contacts storage.
process.env.NEXT_PUBLIC_SUPABASE_URL = "http://localhost:8792";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "answer-tools-test-key";

function assertClosedTools(html: string, names: string[]) {
  for (const name of names) {
    const button = html.match(new RegExp(`<button[^>]*data-muxi-control="${name}"[^>]*>`))?.[0];
    assert.ok(button, `${name} has a discoverable opening button`);
    assert.match(button, /type="button"/);
    assert.match(button, /aria-expanded="false"/);
    const panel = button.match(/aria-controls="([^"]+)"/)?.[1];
    assert.ok(panel, `${name} identifies its panel`);
    const escapedId = panel.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    assert.match(html, new RegExp(`<div(?=[^>]*\\bid="${escapedId}")(?=[^>]*\\bhidden="")[^>]*>`), `${name} starts with its panel hidden`);
  }
}

test("writing tools start closed for empty answers and restored code drafts in both languages", () => {
  for (const lang of ["he", "en"] as const) {
    for (const value of ["", formatTechnicalAnswer("Saved explanation", "int n = 7;", "c")]) {
      let changes = 0;
      const html = renderToStaticMarkup(createElement(AnswerEditor, {
        value, onChange: () => { changes += 1; }, lang, disabled: false,
        codeLanguage: "c", starterCode: "int main() {}",
      }));
      assertClosedTools(html, ["explanation-open", "code-open"]);
      assert.equal(changes, 0, "opening the question does not modify the draft");
      if (value) {
        assert.match(html, />Saved explanation<\/textarea>/);
        assert.equal(html.match(new RegExp(lang === "he" ? "יש תוכן" : "Has content", "g"))?.length, 2,
          "both folded tools disclose that draft content is already present");
      }
      assert.doesNotMatch(html, /data-muxi-control="code-language"/, "heavy editor is deferred until requested");
    }
  }
});

test("an explicit code demonstration opt-in still opens code without exposing explanation", () => {
  const html = renderToStaticMarkup(createElement(AnswerEditor, {
    value: "", onChange: () => {}, lang: "en", disabled: false,
    codeLanguage: "c", starterCode: null, initiallyShowCode: true,
  }));
  assertClosedTools(html, ["explanation-open"]);
  assert.match(html, /aria-expanded="true" aria-controls="[^"]+-code"/);
  assert.match(html, /data-muxi-control="code-language"/);
});

test("circuit and image tools stay closed even for existing visual drafts", async () => {
  const { VisualAnswer } = await import("../src/components/visual-answer");
  const saved: Visual = {
    circuit: { version: 1, parts: [makePart("input", 0)], wires: [] },
    images: [{ path: "user/attempt/image.jpg", name: "saved-answer.jpg", mime: "image/jpeg", size: 100 }],
  };
  for (const lang of ["he", "en"] as const) {
    for (const value of [emptyVisual(), saved]) {
      let changes = 0;
      const html = renderToStaticMarkup(createElement(VisualAnswer, {
        value, onChange: () => { changes += 1; }, lang, attemptId: "attempt", userId: "user",
      }));
      assertClosedTools(html, ["circuit-open", "photos-open"]);
      assert.equal(changes, 0);
      assert.doesNotMatch(html, /class="answer-images"/, "private image loading waits until images are opened");
    }
  }
});

test("submitted visual answers remain readable without editing controls", async () => {
  const { VisualAnswer } = await import("../src/components/visual-answer");
  const html = renderToStaticMarkup(createElement(VisualAnswer, {
    value: {
      circuit: null,
      images: [{ path: "user/attempt/image.jpg", name: "saved-answer.jpg", mime: "image/jpeg", size: 100 }],
    }, lang: "en",
  }));
  assert.match(html, /class="answer-images"/);
  assert.match(html, /saved-answer\.jpg/);
  assert.doesNotMatch(html, /data-muxi-control="(?:circuit-open|photos-open)"/);
});
