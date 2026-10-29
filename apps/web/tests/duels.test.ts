import assert from "node:assert/strict";
import test from "node:test";
import { demoDuelClient, sampleDemoQuestions } from "../src/lib/duel-demo";
import { inviteCode, quizSecondsLeft } from "../src/lib/duel-types";
import data from "../src/components/duels/quiz-demo-data.json";
import { demoAvatarClient } from "../src/lib/avatar-demo";

function storage() {
  const items = new Map<string, string>();
  Object.defineProperty(globalThis, "sessionStorage", { configurable: true, value: { getItem: (k: string) => items.get(k) ?? null, setItem: (k: string, v: string) => items.set(k, v) } });
}

test("a preview avatar saved in Muxi's shop appears in new and resumed demonstration games", async () => {
  storage();
  const wardrobe = demoAvatarClient();
  await wardrobe.buy("aurora");
  const config = { component: "xor", color: "mint", skin: "aurora" };
  await wardrobe.save(config);
  const api = demoDuelClient();
  const duel = await api.create("he");
  assert.deepEqual(duel.me.avatar, config);
  assert.deepEqual((await demoDuelClient().get(duel.id)).me.avatar, config);
  const updated = { component: "dff", color: "coral", skin: "classic" };
  await wardrobe.save(updated);
  assert.deepEqual((await api.get(duel.id)).me.avatar, updated);
});

test("question selection samples distinct sources, then one variant per source", () => {
  for (let i = 0; i < 20; i++) {
    const chosen = sampleDemoQuestions(data.questions);
    assert.equal(chosen.length, 5);
    assert.equal(new Set(chosen.map(q => q.source_key)).size, 5);
    assert.ok(chosen.every(q => q.variant >= 1 && q.variant <= 5));
  }
});

test("preview plays through readiness and scoring, reveals explanations only on settlement and resumes after reload", async () => {
  storage(); let time = 1_800_000_000_000;
  const api = demoDuelClient(() => time);
  const open = await api.create("he");
  assert.equal((await api.wallet("he")).balance, 45);
  assert.equal(open.quiz?.current, null);
  time += 2000;
  const lobby = await api.get(open.id);
  assert.equal(lobby.status, "active"); assert.equal(lobby.deadline, null);
  assert.equal(lobby.quiz?.current, null);
  await api.ready(open.id);
  time += 4000;
  let duel = await api.get(open.id);
  assert.ok(duel.started_at);
  assert.equal(duel.quiz?.seconds_left, 60);
  assert.equal(duel.quiz?.review.length, 0);
  assert.ok(!("correct" in duel.quiz!.current!));
  const selected: string[] = [];
  for (let i = 0; i < 5; i++) {
    const question = duel.quiz!.current!;
    selected.push(question.key);
    const answer = data.questions.find(q => q.key === question.key)!;
    time += 1000;
    duel = await api.answer(open.id, answer.correct, i);
  }
  assert.equal(duel.quiz?.finished, true);
  assert.equal(duel.status, "active");
  assert.equal(duel.quiz?.review.length, 0);
  time += 20000;
  // New client restores the same selected variants and persisted submissions.
  const reloaded = demoDuelClient(() => time);
  duel = await reloaded.get(open.id);
  assert.equal(duel.status, "settled"); assert.equal(duel.won, true);
  assert.deepEqual(duel.quiz?.review.map(q => q.key), selected);
  assert.equal(duel.quiz?.review.length, 5);
  assert.equal((await reloaded.wallet("he")).balance, 55);
  await reloaded.get(open.id);
  assert.equal((await reloaded.wallet("he")).balance, 55, "payout is applied once");
});

test("preview cancellation refunds once and timeouts reject stale selections", async () => {
  storage(); let time = 1_800_000_000_000;
  const api = demoDuelClient(() => time);
  const cancelled = await api.create("en");
  await api.cancel(cancelled.id); await api.cancel(cancelled.id);
  assert.equal((await api.wallet("en")).balance, 50);
  const open = await api.create("en"); time += 4000; await api.get(open.id); await api.ready(open.id);
  time += 4000; await api.get(open.id);
  time += 61000;
  const caughtUp = await api.get(open.id);
  assert.equal(caughtUp.quiz?.answers[0].choice, null);
  assert.equal(caughtUp.quiz?.current?.index, 1);
  await assert.rejects(api.answer(open.id, 0, 0), /question changed/);
});

test("timer uses monotonic elapsed time and invite fields accept codes or links", () => {
  assert.equal(quizSecondsLeft(60, 1000, 11500), 50);
  assert.equal(quizSecondsLeft(60, 1000, 100000), 0);
  assert.equal(inviteCode(" https://example.com/duel/abcdefgh?x=1 "), "abcdefgh");
  assert.equal(inviteCode(" abcdefgh "), "abcdefgh");
});
