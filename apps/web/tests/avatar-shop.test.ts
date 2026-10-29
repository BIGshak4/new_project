import assert from "node:assert/strict";
import { afterEach, before, mock, test } from "node:test";
import { readFileSync } from "node:fs";
import catalog from "../src/lib/avatar-catalog.json";
import { demoAvatarClient, getDemoAvatar } from "../src/lib/avatar-demo";
import { AVATAR_COLORS, DEFAULT_AVATAR } from "../src/lib/avatar-types";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "test-publishable-key";
let client: typeof import("../src/lib/avatar-api");
let supabase: (typeof import("../src/lib/supabase"))["supabase"];
before(async () => { client = await import("../src/lib/avatar-api"); ({ supabase } = await import("../src/lib/supabase")); });
afterEach(() => mock.restoreAll());

function storage() {
  const items = new Map<string, string>();
  Object.defineProperty(globalThis, "sessionStorage", { configurable: true, value: { getItem: (key: string) => items.get(key) ?? null, setItem: (key: string, value: string) => items.set(key, value) } });
}

test("preview catalog and avatar colors match the server's canonical catalog", () => {
  const source = JSON.parse(readFileSync(new URL("../../../backend/seeds/avatar_cosmetics.json", import.meta.url), "utf8"));
  assert.deepEqual(catalog, source);
  assert.deepEqual(Object.fromEntries(catalog.colors.map(color => [color.key, color.hex])), AVATAR_COLORS);
  assert.equal(catalog.skins.find(skin => skin.key === "classic")!.price, 0);
});

test("trying or saving an unowned skin cannot bypass purchase; duplicate demo buys debit once", async () => {
  storage(); const api = demoAvatarClient();
  const before = await api.get();
  assert.equal(before.balance, 160);
  await assert.rejects(() => api.save({ ...DEFAULT_AVATAR, skin: "gold" }));
  assert.deepEqual((await api.get()).avatar, DEFAULT_AVATAR);
  const after = await api.buy("gold");
  assert.equal(after.balance, 20);
  assert.ok(after.owned_skins.includes("gold"));
  assert.equal((await api.buy("gold")).balance, 20);
  await api.save({ component: "xor", color: "mint", skin: "gold" });
  assert.deepEqual(getDemoAvatar(), { component: "xor", color: "mint", skin: "gold" });
  assert.deepEqual((await demoAvatarClient().get()).avatar, getDemoAvatar());
  await assert.rejects(() => api.buy("cosmic"), (error: unknown) => (error as { status: number }).status === 402);
  assert.equal((await api.get()).balance, 20);
});

test("real wardrobe calls bind to the account and submit catalog identifiers rather than price or ownership", async () => {
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "alice-token", user: { id: "alice" } } }, error: null }));
  const payload = await demoAvatarClient().get();
  const calls: { url: string; init: RequestInit }[] = [];
  mock.method(globalThis, "fetch", async (url: string, init: RequestInit) => { calls.push({ url, init }); return Response.json(payload); });
  const api = client.avatarApi("alice", "https://api.example");
  await api.get(); await api.save({ component: "xor", color: "mint", skin: "classic" }); await api.buy("aurora");
  assert.deepEqual(calls.map(call => call.init.method), ["GET", "PUT", "POST"]);
  assert.equal(calls[2].url, "https://api.example/v1/me/avatar/buy");
  assert.deepEqual(JSON.parse(calls[1].init.body as string), { component: "xor", color: "mint", skin: "classic" });
  assert.deepEqual(JSON.parse(calls[2].init.body as string), { skin: "aurora" });
  for (const call of calls) {
    assert.equal((call.init.headers as Record<string,string>).Authorization, "Bearer alice-token");
    assert.equal(call.init.cache, "no-store");
    assert.ok(!String(call.init.body).includes("user_id"));
    assert.ok(!String(call.init.body).includes("price"));
  }
});

test("switching accounts prevents old-account wardrobe reads and writes before transmission", async () => {
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "bob-token", user: { id: "bob" } } }, error: null }));
  const fetch = mock.method(globalThis, "fetch", async () => Response.json({}));
  const api = client.avatarApi("alice", "https://api.example");
  for (const request of [() => api.get(), () => api.save(DEFAULT_AVATAR), () => api.buy("gold")])
    await assert.rejects(request, (error: unknown) => error instanceof client.AvatarApiError && error.code === "unauthenticated");
  assert.equal(fetch.mock.callCount(), 0);
});

test("an account switch while a request is in flight prevents exposing its response", async () => {
  let count = 0;
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "token", user: { id: count++ === 0 ? "alice" : "bob" } } }, error: null }));
  mock.method(globalThis, "fetch", async () => Response.json(await demoAvatarClient().get()));
  await assert.rejects(() => client.avatarApi("alice", "https://api.example").get(), (error: unknown) => error instanceof client.AvatarApiError && error.code === "unauthenticated");
});

test("unconfirmed purchases are never automatically retried or presented as a successful empty wallet", async () => {
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "token", user: { id: "alice" } } }, error: null }));
  const fetch = mock.method(globalThis, "fetch", async () => { throw new Error("connection lost"); });
  await assert.rejects(() => client.avatarApi("alice", "https://api.example").buy("gold"), (error: unknown) => error instanceof client.AvatarApiError && error.code === "network");
  assert.equal(fetch.mock.callCount(), 1);
  mock.restoreAll();
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "token", user: { id: "alice" } } }, error: null }));
  mock.method(globalThis, "fetch", async () => Response.json({}));
  await assert.rejects(() => client.avatarApi("alice", "https://api.example").get(), (error: unknown) => error instanceof client.AvatarApiError && error.code === "invalid_response");
});
