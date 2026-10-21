import assert from "node:assert/strict";
import { afterEach, before, mock, test } from "node:test";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "test-publishable-key";
let client: typeof import("../src/lib/practice-api");
let supabase: (typeof import("../src/lib/supabase"))["supabase"];
before(async () => { client = await import("../src/lib/practice-api"); ({ supabase } = await import("../src/lib/supabase")); });
afterEach(() => mock.restoreAll());

test("fundamentals requests bind to the expected account without transmitting caller-supplied ownership", async () => {
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "alice-token", user: { id: "alice" } } }, error: null }));
  const calls: { url: string; init: RequestInit }[] = [];
  mock.method(globalThis, "fetch", async (url: string, init: RequestInit) => { calls.push({ url, init }); return Response.json({ completed: [], removed: true }); });
  const api = client.practiceApi("https://api.example");
  await api.fundamentalsProgress("alice");
  await api.completeFundamental("alice", "quick-hw-01", "a".repeat(64));
  await api.resetFundamental("alice", "quick-hw-01");
  assert.deepEqual(calls.map(call => call.init.method), ["GET", "PUT", "DELETE"]);
  assert.equal(calls[0].url, "https://api.example/v1/fundamentals/progress");
  assert.deepEqual(JSON.parse(calls[1].init.body as string), { content_revision: "a".repeat(64) });
  for (const call of calls) {
    assert.equal((call.init.headers as Record<string, string>).Authorization, "Bearer alice-token");
    assert.equal(call.init.cache, "no-store");
    assert.equal(call.url.includes("alice"), false);
    assert.equal(String(call.init.body).includes("user_id"), false);
  }
});

test("switching accounts before the token is read refuses every old-account history operation", async () => {
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "bob-token", user: { id: "bob" } } }, error: null }));
  const fetch = mock.method(globalThis, "fetch", async () => Response.json({}));
  const api = client.practiceApi("https://api.example");
  for (const request of [() => api.fundamentalsProgress("alice"), () => api.completeFundamental("alice", "quick-hw-01", "a".repeat(64)), () => api.resetFundamental("alice", "quick-hw-01")])
    await assert.rejects(request, (error: unknown) => error instanceof client.PracticeApiError && error.code === "unauthenticated");
  assert.equal(fetch.mock.callCount(), 0);
});

test("a changed content version remains an actionable save error without an automatic replay", async () => {
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "alice-token", user: { id: "alice" } } }, error: null }));
  const fetch = mock.method(globalThis, "fetch", async () => Response.json({ error: { code: "stale_version", message: "reload" } }, { status: 409 }));
  await assert.rejects(() => client.practiceApi("https://api.example").completeFundamental("alice", "quick-hw-01", "0".repeat(64)),
    (error: unknown) => error instanceof client.PracticeApiError && error.code === "stale_version");
  assert.equal(fetch.mock.callCount(), 1);
});
