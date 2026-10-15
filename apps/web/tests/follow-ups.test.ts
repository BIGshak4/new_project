import assert from "node:assert/strict";
import { before, test } from "node:test";
import { createElement, type ComponentProps } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { Attempt } from "../src/lib/practice-api";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "test-publishable-key";
let FollowUps: typeof import("../src/components/follow-ups")["FollowUps"];
before(async () => { ({ FollowUps } = await import("../src/components/follow-ups")); });
const noop = () => {};
function render(overrides: Partial<Attempt> = {}, props: Partial<ComponentProps<typeof FollowUps>> = {}) {
  const attempt = {
    status: "in_progress", follow_ups: [],
    pending_follow_up: { turn: 1, question: "Why?", action: "probe", question_pending: false },
    ...overrides,
  } as Attempt;
  return renderToStaticMarkup(createElement(FollowUps, {
    attempt, lang: "en", value: "", onChange: noop, onSubmit: noop, onSkip: noop,
    disabled: false, busy: false, resend: false, ...props,
  }));
}
function skipButton(html: string) {
  return html.match(/<button[^>]*>Skip (?:this follow-up|to the next question)<\/button>/)?.[0];
}

test("a skipped turn remains visible without a grade, answer, or XP", () => {
  const html = render({ status: "done", pending_follow_up: null, follow_ups: [{
    turn: 1, question: "Why?", action: "probe", created_at: "", skipped: true, submission: null,
  }] });
  assert.match(html, /Skipped/);
  assert.match(html.replace(/<[^>]*>/g, ""), /Why\?/);
  assert.doesNotMatch(html, /band-|xp-pill|follow-up-answer|textarea/);
});

test("skip is available even while follow-up wording is being written", () => {
  const html = render({ pending_follow_up: { turn: 1, question: "", question_pending: true } as Attempt["pending_follow_up"] });
  assert.match(html, /Writing your follow-up question/);
  assert.match(html, /<textarea[^>]*disabled/);
  assert.ok(skipButton(html));
  assert.doesNotMatch(skipButton(html)!, /disabled/);
});

test("unsafe skip states remain disabled and demo attempts offer no skip", () => {
  for (const props of [{ disabled: true }, { busy: true }, { resend: true }, { skipDisabled: true }]) {
    assert.match(skipButton(render({}, props))!, /disabled/);
  }
  assert.match(skipButton(render({ status: "evaluating" }))!, /disabled/);
  assert.equal(skipButton(render({}, { demo: true })), undefined);
});

test("the skip action names the next question only when a suggestion exists", () => {
  assert.match(skipButton(render())!, /Skip this follow-up/);
  assert.match(skipButton(render({ next_question: { key: "next" } as Attempt["next_question"] }))!, /Skip to the next question/);
  assert.match(render({}, { lang: "he" }), /דילוג על שאלת ההמשך/);
});

test("answered follow-ups retain their saved grade and XP", () => {
  const html = render({ pending_follow_up: null, follow_ups: [{
    turn: 1, question: "Why?", action: "probe", created_at: "", submission: {
      answer: "Because", status: "done", band: "STRONG", xp_earned: 12, summary: "Clear reasoning",
    },
  }] } as Partial<Attempt>);
  assert.match(html, /Because/);
  assert.match(html, /band-strong/);
  assert.match(html, /\+12 XP/);
  assert.match(html, /Clear reasoning/);
});

test("mixed-language follow-up expressions stay left-to-right in the question, answer and feedback", () => {
  const question = "מדוע A XOR B שווה לאפס?";
  const html = render({ pending_follow_up: null, follow_ups: [{
    turn: 1, question, action: "probe", created_at: "", submission: {
      answer: "כי A = B ולכן XOR מתאפס", status: "done", band: "STRONG", xp_earned: 0,
      summary: "הסבר נכון עבור A XOR B בשוויון",
    },
  }] } as Partial<Attempt>, { lang: "he" });
  assert.match(html, /מדוע <bdi dir="ltr">A XOR B<\/bdi> שווה לאפס\?/);
  assert.match(html, /כי <bdi dir="ltr">A = B<\/bdi> ולכן <bdi dir="ltr">XOR<\/bdi> מתאפס/);
  assert.match(html, /הסבר נכון עבור <bdi dir="ltr">A XOR B<\/bdi> בשוויון/);
  const pending = render({ pending_follow_up: { turn: 1, question } as Attempt["pending_follow_up"] }, { lang: "he" });
  assert.match(pending, /מדוע <bdi dir="ltr">A XOR B<\/bdi>/);
});
