import assert from "node:assert/strict";
import { afterEach, before, mock, test } from "node:test";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "test-publishable-key";
let client: typeof import("../src/lib/practice-api");
let supabase: (typeof import("../src/lib/supabase"))["supabase"];
before(async () => { client = await import("../src/lib/practice-api"); ({ supabase } = await import("../src/lib/supabase")); });
afterEach(() => mock.restoreAll());

test("deleting interview history uses authenticated DELETE and sends no caller ownership", async () => {
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "alice-token", user: { id: "alice" } } }, error: null }));
  const calls: { url: string; init: RequestInit }[] = [];
  mock.method(globalThis, "fetch", async (url: string, init: RequestInit) => { calls.push({ url, init }); return Response.json({ deleted: true }); });
  assert.deepEqual(await client.practiceApi("https://api.example").deleteInterview("interview-id", "alice"), { deleted: true });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "https://api.example/v1/interviews/interview-id");
  assert.equal(calls[0].init.method, "DELETE");
  assert.equal(calls[0].init.body, undefined);
  assert.equal((calls[0].init.headers as Record<string, string>).Authorization, "Bearer alice-token");
});

test("an account change before deletion refuses the stale account action", async () => {
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "bob-token", user: { id: "bob" } } }, error: null }));
  const fetch = mock.method(globalThis, "fetch", async () => Response.json({ deleted: true }));
  await assert.rejects(() => client.practiceApi("https://api.example").deleteInterview("interview-id", "alice"),
    (error: unknown) => error instanceof client.PracticeApiError && error.code === "unauthenticated");
  assert.equal(fetch.mock.callCount(), 0);
});
