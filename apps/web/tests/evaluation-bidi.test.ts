import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { NextQuestion, Submission } from "../src/lib/practice-api";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "test-publishable-key";

test("assessment prose preserves technical expressions inside Hebrew across feedback sections", async () => {
  const { EvaluationPanel } = await import("../src/components/evaluation-panel");
  const mixed = "הביטוי A XOR B תקין";
  const submission: Submission = {
    revision: 1, key: "feedback-bidi", turn: 0, answer: "A XOR B",
    accepted_at: "2026-10-15T10:00:00Z", evaluated_at: "2026-10-15T10:00:01Z",
    follow_up: null, assessed_by: "model", model: "test", replayed: false,
    status: "done", band: "STRONG", summary: mixed,
    key_points_hit: [mixed], key_points_missed: [mixed], flags: [], evidence: "full",
    tip: { key: "tip", text: mixed }, card: {
      what_happened: mixed, why_it_matters: mixed, next_step: mixed, your_reasoning_vs_reference: mixed,
    },
    check: { type: "truth_table", passed: false, detail: mixed, mismatches: [{ inputs: { A: 1, B: 0 }, expected: 1, got: 0 }] },
  };
  const html = renderToStaticMarkup(createElement(EvaluationPanel, { submission, lang: "he" }));
  assert.ok((html.match(/הביטוי <bdi dir="ltr">A XOR B<\/bdi> תקין/g) ?? []).length >= 7);
  assert.match(html, /<td dir="ltr"><bdi dir="ltr">A=1, B=0<\/bdi><\/td>/);
  assert.doesNotMatch(html, /הביטוי A XOR B תקין/);
});

test("next-question titles, focus and reasons keep their expression order", async () => {
  const { NextUpCard } = await import("../src/components/evaluation-panel");
  const next = {
    key: "q", title: "בדיקת A XOR B", focus: "הסבר על A XOR B",
    reason: "כדי לתרגל A XOR B שוב", subject: "digital_logic", difficulty: 2, why: "reinforce",
  } as NextQuestion;
  const html = renderToStaticMarkup(createElement(NextUpCard, { next, lang: "he", onStart: () => {} }));
  assert.equal((html.match(/<bdi dir="ltr">A XOR B<\/bdi>/g) ?? []).length, 3);
  assert.match(html.replace(/<[^>]*>/g, ""), /בדיקת A XOR B/);
});

test("new plan-based recommendation reasons render readable badges in both languages", async () => {
  const { NextUpCard } = await import("../src/components/evaluation-panel");
  const labels = {
    map: { he: "מיומנות שטרם נבדקה", en: "Unassessed skill" },
    same_skill: { he: "עוד באותה מיומנות", en: "More on this skill" },
  } as const;
  for (const why of ["map", "same_skill"] as const) {
    for (const lang of ["he", "en"] as const) {
      const next: NextQuestion = {
        key: "q", title: "Question", subject: "digital_logic", skill: "gates", difficulty: 2,
        why, reason: "The next planned skill to practise.",
      };
      const html = renderToStaticMarkup(createElement(NextUpCard, { next, lang, onStart: () => {} }));
      assert.ok(html.includes(`<span class="badge why-${why}">${labels[why][lang]}</span>`));
      assert.doesNotMatch(html, new RegExp(`>\\s*${why}\\s*<`));
    }
  }
});
