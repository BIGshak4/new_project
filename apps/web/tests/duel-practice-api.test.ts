import assert from "node:assert/strict";
import test from "node:test";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://fixture.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "fixture-public-key";
const modules = Promise.all([import("../src/lib/duel-api"), import("../src/lib/supabase")]);
const session = (id: string) => ({ data: { session: { access_token: "local-fixture-token", user: { id } } }, error: null });

test("real practice fetches bank content and sends only the round token and selected option for checking", async t => {
  const [{ duelApi }, { supabase }] = await modules;
  t.mock.method(supabase.auth, "getSession", async () => session("owner"));
  const calls: { url: string; init?: RequestInit }[] = [];
  t.mock.method(globalThis, "fetch", async (url: string, init?: RequestInit) => {
    calls.push({ url, init });
    return new Response(JSON.stringify(init?.method === "GET" ? { round_token: "signed-round", language: "he", question: { choices: ["a", "b", "c", "d"] } } : { correct: false, correct_index: 2, explanation: "Bank explanation" }), { status: 200 });
  });
  const practice = duelApi("owner", "https://fixture.invalid").practice!;
  const round = await practice.start("he");
  assert.equal(calls[0].url, "https://fixture.invalid/v1/duels/practice?language=he");
  assert.equal(calls[0].init?.cache, "no-store");
  assert.equal((calls[0].init?.headers as Record<string, string>).Authorization, "Bearer local-fixture-token");
  assert.ok(!("correct" in round.question));
  const result = await practice.answer(round.round_token, 1);
  assert.equal(calls[1].url, "https://fixture.invalid/v1/duels/practice/answer");
  assert.deepEqual(JSON.parse(String(calls[1].init?.body)), { round_token: "signed-round", choice: 1 });
  assert.equal(result.correct, false);
  assert.equal(result.explanation, "Bank explanation");
});

test("practice cannot start while signed out and a response for a switched account is rejected", async t => {
  const [{ duelApi }, { supabase }] = await modules;
  let id = "other";
  t.mock.method(supabase.auth, "getSession", async () => session(id));
  const fetchMock = t.mock.method(globalThis, "fetch", async () => {
    id = "other";
    return new Response(JSON.stringify({ question: { prompt: "private round" } }), { status: 200 });
  });
  const practice = duelApi("owner", "https://fixture.invalid").practice!;
  await assert.rejects(practice.start("en"), { code: "unauthenticated" });
  assert.equal(fetchMock.mock.callCount(), 0);
  id = "owner";
  await assert.rejects(practice.start("en"), { code: "unauthenticated" });
  assert.equal(fetchMock.mock.callCount(), 1);
});
