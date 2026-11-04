import assert from "node:assert/strict";
import { afterEach, before, mock, test } from "node:test";
import { AVATAR_UPDATED_EVENT, AvatarRefreshGuard, readAvatarUpdate } from "../src/lib/avatar-events";
import { demoAvatarClient, getDemoAvatar } from "../src/lib/avatar-demo";
import { DEFAULT_AVATAR, type AvatarConfig } from "../src/lib/avatar-types";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "test-publishable-key";
let client: typeof import("../src/lib/avatar-api");
let supabase: (typeof import("../src/lib/supabase"))["supabase"];
before(async () => { client = await import("../src/lib/avatar-api"); ({ supabase } = await import("../src/lib/supabase")); });
const savedWindow = Object.getOwnPropertyDescriptor(globalThis, "window");
const savedStorage = Object.getOwnPropertyDescriptor(globalThis, "sessionStorage");
afterEach(() => {
  mock.restoreAll();
  if (savedWindow) Object.defineProperty(globalThis, "window", savedWindow); else Reflect.deleteProperty(globalThis, "window");
  if (savedStorage) Object.defineProperty(globalThis, "sessionStorage", savedStorage); else Reflect.deleteProperty(globalThis, "sessionStorage");
});

function browser() {
  const target = new EventTarget();
  const values = new Map<string, string>();
  Object.defineProperty(globalThis, "window", { configurable: true, value: target });
  Object.defineProperty(globalThis, "sessionStorage", { configurable: true, value: { getItem: (key: string) => values.get(key) ?? null, setItem: (key: string, value: string) => values.set(key, value) } });
  return target;
}

test("avatar events are scoped to the current account and never mix demo with real outfits", () => {
  const update = { userId: "alice", demo: false, avatar: { ...DEFAULT_AVATAR, color: "mint" } };
  assert.deepEqual(readAvatarUpdate(update, "alice", false), update.avatar);
  assert.equal(readAvatarUpdate(update, "bob", false), null);
  assert.equal(readAvatarUpdate(update, undefined, false), null);
  assert.equal(readAvatarUpdate(update, "alice", true), null);
  const demo = { ...update, userId: null, demo: true };
  assert.deepEqual(readAvatarUpdate(demo, undefined, true), update.avatar);
  assert.equal(readAvatarUpdate(demo, "alice", false), null);
  for (const avatar of [null, { ...DEFAULT_AVATAR, component: "unknown" }, { ...DEFAULT_AVATAR, color: "constructor" }, { ...DEFAULT_AVATAR, skin: {} }]) {
    assert.equal(readAvatarUpdate({ ...update, avatar }, "alice", false), null);
  }
});

test("a confirmed outfit invalidates an in-flight read and cleanup invalidates later reads", async () => {
  const guard = new AvatarRefreshGuard();
  let avatar: AvatarConfig = DEFAULT_AVATAR;
  let resolve!: (value: AvatarConfig) => void;
  const old = new Promise<AvatarConfig>(done => { resolve = done; });
  const current = guard.start();
  const reading = old.then(value => { if (current()) avatar = value; });
  guard.invalidate();
  avatar = { ...DEFAULT_AVATAR, color: "sky" };
  resolve(DEFAULT_AVATAR);
  await reading;
  assert.equal(avatar.color, "sky");
  const earlier = guard.start(), latest = guard.start();
  assert.equal(earlier(), false);
  assert.equal(latest(), true);
  guard.invalidate();
  assert.equal(latest(), false);
});

test("preview saves publish the persisted avatar; unsuccessful changes publish nothing", async () => {
  const target = browser();
  const events: unknown[] = [];
  target.addEventListener(AVATAR_UPDATED_EVENT, event => {
    const detail = (event as CustomEvent).detail;
    assert.deepEqual(detail.avatar, getDemoAvatar());
    events.push(detail);
  });
  const api = demoAvatarClient();
  await api.get();
  await assert.rejects(() => api.save({ ...DEFAULT_AVATAR, skin: "gold" }));
  assert.equal(events.length, 0);
  const next = { ...DEFAULT_AVATAR, color: "mint" };
  await api.save(next);
  assert.deepEqual(events, [{ userId: null, demo: true, avatar: next }]);
});

test("production reads emit nothing; only validated successful mutations publish an outfit", async () => {
  const target = browser();
  const events: unknown[] = [];
  target.addEventListener(AVATAR_UPDATED_EVENT, event => events.push((event as CustomEvent).detail));
  const payload = await demoAvatarClient().get();
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "token", user: { id: "alice" } } }, error: null }));
  mock.method(globalThis, "fetch", async () => Response.json(payload));
  const api = client.avatarApi("alice", "https://api.example");
  await api.get();
  assert.equal(events.length, 0);
  await api.save(DEFAULT_AVATAR);
  assert.deepEqual(events, [{ userId: "alice", demo: false, avatar: payload.avatar }]);
  mock.method(globalThis, "fetch", async () => Response.json({ error: { code: "validation" } }, { status: 422 }));
  await assert.rejects(() => api.save(DEFAULT_AVATAR));
  assert.equal(events.length, 1);
});

test("an account change while decoding a response cannot publish the old account's avatar", async () => {
  const target = browser();
  const events: unknown[] = [];
  target.addEventListener(AVATAR_UPDATED_EVENT, event => events.push((event as CustomEvent).detail));
  const payload = await demoAvatarClient().get();
  let userId = "alice";
  mock.method(supabase.auth, "getSession", async () => ({ data: { session: { access_token: "token", user: { id: userId } } }, error: null }));
  mock.method(globalThis, "fetch", async () => ({ ok: true, json: async () => { userId = "bob"; return payload; } } as Response));
  await assert.rejects(() => client.avatarApi("alice", "https://api.example").save(DEFAULT_AVATAR), (error: unknown) => error instanceof client.AvatarApiError && error.code === "unauthenticated");
  assert.equal(events.length, 0);
});
