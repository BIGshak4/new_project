import assert from "node:assert/strict";
import test from "node:test";
import { readDailyDraft, writeDailyDraft } from "../src/lib/daily-puzzle";
import { emptyCircuit, emptyVisual, makePart } from "../src/lib/circuit";

test("personal daily drafts survive a refresh and stay within their account, day and variant", t => {
  const data = new Map<string, string>();
  const storage = { getItem: (key: string) => data.get(key) ?? null, setItem: (key: string, value: string) => data.set(key, value) };
  const previous = Object.getOwnPropertyDescriptor(globalThis, "localStorage");
  Object.defineProperty(globalThis, "localStorage", { configurable: true, value: storage });
  t.after(() => {
    if (previous) Object.defineProperty(globalThis, "localStorage", previous);
    else Reflect.deleteProperty(globalThis, "localStorage");
  });
  const puzzle = { day: "2026-11-15", id: "alternate-one" };
  const empty = { answer: "", visual: emptyVisual() };
  const saved = { answer: "I would compare the two inputs.", visual: {
    circuit: { ...emptyCircuit(), parts: [makePart("xor", 0)] }, images: [],
  } };
  writeDailyDraft("first", puzzle, saved);
  assert.deepEqual(readDailyDraft("first", puzzle), saved);
  assert.deepEqual(readDailyDraft("second", puzzle), empty);
  assert.deepEqual(readDailyDraft("first", { ...puzzle, id: "another-variant" }), empty);
  assert.deepEqual(readDailyDraft("first", { ...puzzle, day: "2026-11-16" }), empty);
  storage.setItem("jobrun:daily-puzzle:first", JSON.stringify({ ...puzzle, answer: "older browser draft", revealed: true }));
  assert.deepEqual(readDailyDraft("first", puzzle), { ...empty, answer: "older browser draft" });
});

test("daily submissions carry the displayed puzzle and its visual answer while retries only reference the original submission", async t => {
  process.env.NEXT_PUBLIC_SUPABASE_URL = "https://fixture.supabase.co";
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "fixture-public-key";
  const [{ duelApi }, { supabase }] = await Promise.all([import("../src/lib/duel-api"), import("../src/lib/supabase")]);
  t.mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "fixture", user: { id: "first" } } }, error: null }));
  const calls: { url: string; init?: RequestInit }[] = [];
  t.mock.method(globalThis, "fetch", async (url: string, init?: RequestInit) => {
    calls.push({ url, init });
    return init?.method === "GET"
      ? Response.json({ id: "variant", day: "2026-11-15", title: "Test", prompt: "Prompt", subject: "software", expires_at: "2026-11-15T22:00:00Z" })
      : Response.json({ error: { code: "conflict" } }, { status: 409 });
  });
  const client = duelApi("first", "https://fixture.invalid").daily;
  const puzzle = await client.get("he");
  assert.ok(!("solution" in puzzle));
  assert.equal(calls[0].url, "https://fixture.invalid/v1/games/daily-puzzle?language=he");
  assert.equal(calls[0].init?.cache, "no-store");
  const answer = { text: "Use XOR.", visual: { circuit: { ...emptyCircuit(), parts: [makePart("xor", 0)] }, images: [] } };
  await assert.rejects(client.submit("he", puzzle.day, puzzle.id, answer), { status: 409 });
  assert.equal(calls[1].url, "https://fixture.invalid/v1/games/daily-puzzle/submit?language=he");
  assert.deepEqual(JSON.parse(String(calls[1].init?.body)), { day: puzzle.day, id: puzzle.id, answer });
  await assert.rejects(client.retry("he", puzzle.day, puzzle.id), { status: 409 });
  assert.equal(calls[2].url, "https://fixture.invalid/v1/games/daily-puzzle/retry?language=he");
  assert.deepEqual(JSON.parse(String(calls[2].init?.body)), { day: puzzle.day, id: puzzle.id });
  await assert.rejects(client.reveal("en", puzzle.day, puzzle.id), { status: 409 });
  assert.equal(calls[3].url, "https://fixture.invalid/v1/games/daily-puzzle/reveal?language=en");
  assert.deepEqual(JSON.parse(String(calls[3].init?.body)), { day: puzzle.day, id: puzzle.id });
  await client.get("en", puzzle.day);
  assert.equal(calls[4].url, "https://fixture.invalid/v1/games/daily-puzzle?language=en&day=" + puzzle.day);
});
