import { test } from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { QuestionSummary } from "../src/lib/practice-api";

process.env.NEXT_PUBLIC_SUPABASE_URL ??= "http://localhost:8794";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??= "metadata-test-key";
async function renderMetadata(props: { question: QuestionSummary; lang: "he" | "en"; compact?: boolean }) {
  const { QuestionMetadata } = await import("../src/components/question-metadata");
  return renderToStaticMarkup(createElement(QuestionMetadata, props));
}

const question = { category: "hardware", subject: "digital_fundamentals", topics: ["logic_gates", "mux", "logic_gates"],
  reported_companies: ["Intel", "NVIDIA", "Apple", "Marvell", "אינטל"], companies: [], preparation_id: "PREP-001" } as unknown as QuestionSummary;

test("library metadata shows one category and at most three deduplicated company names", async () => {
  for (const lang of ["he", "en"] as const) {
    const html = await renderMetadata({ question, lang, compact: true });
    assert.equal((html.match(/class="company-name"/g) ?? []).length, 3);
    assert.match(html, lang === "he" ? /ועוד 1/ : /\+1 more/);
    assert.doesNotMatch(html, /Marvell|logic gates|mux|Topic:|נושא:/);
    assert.equal((html.match(/class="discipline-label"/g) ?? []).length, 1);
    assert.doesNotMatch(html, /<button|<a /); // the enclosing question row is the single action
  }
});

test("opening a question keeps every company and every distinct related topic by default", async () => {
  const html = await renderMetadata({ question, lang: "he" });
  assert.equal((html.match(/class="company-name"/g) ?? []).length, 4);
  assert.match(html, /Marvell/);
  assert.match(html, /logic gates/);
  assert.match(html, /mux/);
  assert.equal((html.match(/logic gates/g) ?? []).length, 1);
  assert.doesNotMatch(html, /company-more/);
});

test("empty reports do not fabricate names or a more indicator", async () => {
  const html = await renderMetadata({ question: { ...question, reported_companies: [] }, lang: "he", compact: true });
  assert.match(html, /טרם נוסף דיווח/);
  assert.doesNotMatch(html, /company-name|company-more/);
});
