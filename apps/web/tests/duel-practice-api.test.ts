import assert from "node:assert/strict";
import test from "node:test";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://fixture.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "fixture-public-key";
const modules = Promise.all([import("../src/lib/duel-api"), import("../src/lib/supabase")]);
const session = (id: string) => ({ data: { session: { access_token: "local-fixture-token", user: { id } } }, error: null });

test("friend challenges and link invitations use distinct creation payloads and require explicit acceptance", async t => {
  const [{ duelApi }, { supabase }] = await modules;
  t.mock.method(supabase.auth, "getSession", async () => session("owner"));
  const calls: { path: string; method?: string; body?: unknown }[] = [];
  t.mock.method(globalThis, "fetch", async (url: string, init?: RequestInit) => {
    const path = new URL(url).pathname;
    calls.push({ path, method: init?.method, body: init?.body ? JSON.parse(String(init.body)) : undefined });
    if (path.endsWith("/presence")) return new Response(null, { status: 204 });
    return Response.json(path.endsWith("/invitations") ? { invitations: [] } : {});
  });
  const api = duelApi("owner", "https://fixture.invalid");
  await api.create("he", "friend");
  await api.create("en");
  await api.presence();
  await api.invitations();
  await api.accept("roomcode");
  assert.deepEqual(calls, [
    { path: "/v1/duels", method: "POST", body: { language: "he", mode: "quiz", friend_id: "friend" } },
    { path: "/v1/duels", method: "POST", body: { language: "en", mode: "quiz" } },
    { path: "/v1/me/presence", method: "POST", body: {} },
    { path: "/v1/duels/invitations", method: "GET", body: undefined },
    { path: "/v1/duels/accept", method: "POST", body: { code: "roomcode" } },
  ]);
});

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
