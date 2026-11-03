import assert from "node:assert/strict";
import { afterEach, before, mock, test } from "node:test";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "account-test-publishable-key";
let api: typeof import("../src/lib/account-stats-api");
let supabase: (typeof import("../src/lib/supabase"))["supabase"];
before(async () => {
  api = await import("../src/lib/account-stats-api");
  ({ supabase } = await import("../src/lib/supabase"));
});
afterEach(() => mock.restoreAll());
const session = (id: string) => ({ data: { session: { user: { id }, access_token: "access" } }, error: null });
const activity = { timezone: "Asia/Jerusalem", today: "2026-11-03", streak_days: 0, today_count: 0, last_solved_date: null, days: [] };

test("canonical wallet and local-calendar activity retain real zeroes and owner auth", async () => {
  mock.method(supabase.auth, "getSession", async () => session("user"));
  const calls: { url: string; init: RequestInit }[] = [];
  mock.method(globalThis, "fetch", async (url: string, init: RequestInit) => {
    calls.push({ url, init }); return Response.json(url.includes("/activity") ? activity : { enabled: true, balance: 0 });
  });
  const client = api.accountStatsApi("user", "https://api.example");
  const signal = new AbortController().signal;
  assert.equal((await client.wallet("he", signal)).balance, 0);
  assert.equal((await client.activity("Asia/Jerusalem", signal)).streak_days, 0);
  assert.equal(calls[0].url, "https://api.example/v1/me/coins?language=he");
  assert.equal(new URL(calls[1].url).searchParams.get("timezone"), "Asia/Jerusalem");
  assert.equal((calls[0].init.headers as Record<string, string>).Authorization, "Bearer access");
  assert.equal(calls[0].init.cache, "no-store");
});

test("an account change prevents an old account read before transmission", async () => {
  mock.method(supabase.auth, "getSession", async () => session("other"));
  const fetch = mock.method(globalThis, "fetch", async () => Response.json(activity));
  await assert.rejects(api.accountStatsApi("user", "https://api.example").activity("UTC", new AbortController().signal), /account changed/);
  assert.equal(fetch.mock.callCount(), 0);
});

test("an in-flight response cannot publish into a different account", async () => {
  let current = "user";
  mock.method(supabase.auth, "getSession", async () => session(current));
  mock.method(globalThis, "fetch", async () => { current = "other"; return Response.json({ enabled: true, balance: 300 }); });
  await assert.rejects(api.accountStatsApi("user", "https://api.example").wallet("en", new AbortController().signal), /account changed/);
});

test("unavailable or malformed balances and days never masquerade as a successful zero", async () => {
  mock.method(supabase.auth, "getSession", async () => session("user"));
  const fetch = mock.method(globalThis, "fetch", async () => Response.json({ balance: null, enabled: true }));
  const client = api.accountStatsApi("user", "https://api.example"), signal = new AbortController().signal;
  await assert.rejects(client.wallet("he", signal), /Incomplete wallet/);
  fetch.mock.mockImplementation(async () => Response.json({ ...activity, today_count: -1 }));
  await assert.rejects(client.activity("UTC", signal), /Incomplete activity/);
  fetch.mock.mockImplementation(async () => Response.json({ error: "unavailable" }, { status: 503 }));
  await assert.rejects(client.wallet("he", signal), /could not complete/);
});
