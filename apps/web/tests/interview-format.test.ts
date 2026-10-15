import { test } from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { PracticeApi } from "../src/lib/practice-api";

// VisualAnswer imports the shared Supabase client. Rendering the lobby needs no
// network, and this local-only configuration makes the component import inert.
process.env.NEXT_PUBLIC_SUPABASE_URL = "http://localhost:8792";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "interview-format-test-key";

async function lobby(lang: "he" | "en", initialDuration?: number | null) {
  const { InterviewSession } = await import("../src/components/interview-session");
  return renderToStaticMarkup(createElement(InterviewSession, {
    api: {} as PracticeApi,
    lang,
    userId: "format-preview",
    demo: false,
    initialDuration,
    onStarted: () => {},
    onBack: () => {},
  }));
}

test("interview format is explicit before the start action in both languages", async () => {
  const hebrew = await lobby("he");
  assert.match(hebrew, /ראיון בכתב/);
  assert.match(hebrew, /טקסט או בקוד/);
  assert.match(hebrew, /שרטוטים ותמונות/);
  assert.match(hebrew, /אין שיחה קולית ואין צורך במיקרופון/);
  assert.ok(hebrew.indexOf("אין שיחה קולית") < hebrew.indexOf("להתחיל ראיון בכתב"));
  const english = await lobby("en");
  assert.match(english, /Written interview/);
  assert.match(english, /text or code/);
  assert.match(english, /diagrams or photos/);
  assert.ok(english.indexOf("There is no voice call") < english.indexOf("Start written interview"));
  for (const html of [hebrew, english]) {
    assert.doesNotMatch(html, /lucide-mic/);
    assert.match(html, /role="radiogroup" aria-label="[^"]+"/);
  }
});

test("a planned interview opens with its supported duration, while absent or unsupported values use 30", async () => {
  for (const [initial, selected] of [[20, 20], [30, 30], [45, 45], [undefined, 30], [null, 30], [10, 30], [NaN, 30]] as const) {
    const html = await lobby("en", initial);
    const selectedRadio = html.match(/<button[^>]*role="radio"[^>]*aria-checked="true"[^>]*><strong>(\d+)<\/strong>/g) ?? [];
    assert.equal(selectedRadio.length, 1);
    assert.match(selectedRadio[0], new RegExp(`<strong>${selected}</strong>`));
  }
});
