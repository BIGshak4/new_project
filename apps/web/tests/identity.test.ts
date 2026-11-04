import { before, test } from "node:test";
import assert from "node:assert/strict";
import { IdentityApiError, friendName, identityErrorMessage, normalizeFriendCode, normalizeUsername, readFriends, readIdentity, readUsernameAvailability, validFriendCode, validUsernameFormat } from "../src/lib/identity-types";
import type { IdentityAuth } from "../src/lib/identity-api";

let identityApi: typeof import("../src/lib/identity-api").identityApi;
let usernameAvailability: typeof import("../src/lib/identity-api").usernameAvailability;
before(async () => {
  process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "identity-test-publishable-key";
  ({ identityApi, usernameAvailability } = await import("../src/lib/identity-api"));
});

const identity = { username: "Harel_4", friend_code: "01ABCDEF", can_claim_username: false };
const person = { user_id: "friend-id", username: "שקד", friend_code: "8765ABCD", avatar: { component: "xor", color: "mint", skin: "classic" } };
const list = { friends: [person], incoming: [], outgoing: [] };
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(done => { resolve = done; }); return { promise, resolve }; }
function account(initial = "owner") {
  let owner: string | null = initial;
  const listeners = new Set<(event: string, session: { access_token: string; user: { id: string } } | null) => void>();
  const session = () => owner ? { access_token: `token-${owner}`, user: { id: owner } } : null;
  const auth: IdentityAuth = {
    getSession: async () => ({ data: { session: session() } }),
    onAuthStateChange(callback) { listeners.add(callback); return { data: { subscription: { unsubscribe() { listeners.delete(callback); } } } }; },
  };
  return { auth, switch(next: string | null) { owner = next; for (const callback of listeners) callback("SIGNED_IN", session()); }, listeners };
}

test("username format handles Hebrew and normalized English while rejecting codes, controls and punctuation", () => {
  assert.equal(normalizeUsername("  Ｈarel_4  "), "Harel_4");
  for (const name of ["Harel_4", "שקד_4", "אבג", "ABC", "A".repeat(24)]) assert.equal(validUsernameFormat(name), true, name);
  for (const name of ["", "ab", "12345678", "________", "a b", "a-b", "a@b", "a\u202eb", "A".repeat(25)]) assert.equal(validUsernameFormat(name), false, name);
});

test("friend codes preserve leading zeroes and legacy people get a safe public name", () => {
  assert.equal(normalizeFriendCode(" 01abcdef "), "01ABCDEF");
  assert.equal(validFriendCode("01ABCDEF"), true);
  for (const code of ["1234567", "123456789", "G1234567", "1234 5678"]) assert.equal(validFriendCode(code), false);
  assert.equal(friendName({ username: null, friend_code: "01ABCDEF" }, "he"), "משתמש/ת 01ABCDEF");
  assert.equal(friendName(person, "en"), "שקד");
});

test("incomplete identity, availability and friends responses never become successful empty data", () => {
  assert.deepEqual(readIdentity(identity), identity);
  assert.deepEqual(readFriends(list), list);
  assert.deepEqual(readUsernameAvailability({ available: false, reason: "taken" }), { available: false, reason: "taken" });
  for (const value of [{ ...identity, friend_code: "abc" }, { username: null, friend_code: "01ABCDEF" }]) assert.throws(() => readIdentity(value));
  for (const value of [{ available: true, reason: "taken" }, { available: false, reason: null }, { available: "yes", reason: null }]) assert.throws(() => readUsernameAvailability(value));
  for (const value of [{ friends: [] }, { ...list, friends: [person, person] }, { ...list, friends: [{ ...person, avatar: undefined }] }]) assert.throws(() => readFriends(value));
});

test("identity and friendship writes bind to the account and transmit public identifiers only", async () => {
  const auth = account();
  const original = globalThis.fetch;
  const calls: { url: string; init?: RequestInit }[] = [];
  globalThis.fetch = async (url, init) => { calls.push({ url: String(url), init }); return response(String(url).includes("/identity") ? identity : list); };
  try {
    const api = identityApi("owner", "https://api.example", auth.auth);
    await api.claimUsername(" Ｈarel_4 ");
    await api.requestFriend(" 01abcdef ");
    await api.acceptRequest("request/id");
    await api.declineRequest("request/id");
    await api.cancelRequest("request/id");
    await api.removeFriend("friend/id");
    assert.deepEqual(JSON.parse(calls[0].init?.body as string), { username: "Harel_4" });
    assert.deepEqual(JSON.parse(calls[1].init?.body as string), { friend_code: "01ABCDEF" });
    assert.equal(calls[0].init?.method, "PUT");
    assert.match(calls[2].url, /request%2Fid\/accept$/);
    assert.match(calls[3].url, /request%2Fid\/decline$/);
    assert.equal(calls[4].init?.method, "DELETE");
    assert.match(calls[5].url, /friends\/friend%2Fid$/);
    for (const call of calls) assert.equal(new Headers(call.init?.headers).get("Authorization"), "Bearer token-owner");
    assert.equal(auth.listeners.size, 0, "every request releases its lifecycle listener");
  } finally { globalThis.fetch = original; }
});

test("switching accounts before session resolution prevents an old write from being transmitted", async () => {
  const auth = account();
  const pending = deferred<Awaited<ReturnType<IdentityAuth["getSession"]>>>();
  auth.auth.getSession = () => pending.promise;
  const original = globalThis.fetch;
  let transmitted = 0;
  globalThis.fetch = async () => { transmitted++; return response(identity); };
  try {
    const action = identityApi("owner", "https://api.example", auth.auth).claimUsername("Harel");
    auth.switch("other");
    pending.resolve({ data: { session: { access_token: "old-token", user: { id: "owner" } } } });
    await assert.rejects(action, error => error instanceof IdentityApiError && error.code === "unauthenticated");
    assert.equal(transmitted, 0);
    assert.equal(auth.listeners.size, 0);
  } finally { globalThis.fetch = original; }
});

test("sign-out and returning to the same account cannot reveal an in-flight friends response", async () => {
  const auth = account();
  const pending = deferred<Response>();
  const sent = deferred<void>();
  const original = globalThis.fetch;
  globalThis.fetch = async () => { sent.resolve(); return pending.promise; };
  try {
    const action = identityApi("owner", "https://api.example", auth.auth).friends();
    await sent.promise;
    auth.switch(null); auth.switch("owner");
    pending.resolve(response(list));
    await assert.rejects(action, error => error instanceof IdentityApiError && error.code === "account_changed");
    assert.equal(auth.listeners.size, 0);
  } finally { globalThis.fetch = original; }
});

test("username availability is public and malformed acknowledgements remain errors", async () => {
  const original = globalThis.fetch;
  const urls: string[] = [];
  globalThis.fetch = async (url, init) => { urls.push(String(url)); assert.equal(new Headers(init?.headers).has("Authorization"), false); return response({ available: true, reason: null }); };
  try {
    assert.deepEqual(await usernameAvailability(" שקד_4 ", undefined, "https://api.example"), { available: true, reason: null });
    assert.match(urls[0], /usernames\/availability\?username=/);
    assert.equal(new URL(urls[0]).searchParams.get("username"), "שקד_4");
    globalThis.fetch = async () => response({ available: true, reason: "taken" });
    await assert.rejects(usernameAvailability("Harel", undefined, "https://api.example"), error => error instanceof IdentityApiError && error.code === "invalid_response");
  } finally { globalThis.fetch = original; }
});

test("server error codes have human translations without exposing raw backend messages", () => {
  assert.match(identityErrorMessage(new IdentityApiError("username_taken", "SECRET DATABASE DETAILS"), "he"), /תפוס/);
  assert.match(identityErrorMessage({ code: "username_required" }, "en"), /Personal area/);
  assert.match(identityErrorMessage({ code: "friend_request_received" }, "en"), /incoming requests/);
  assert.doesNotMatch(identityErrorMessage({ code: "unexpected", message: "SECRET DATABASE DETAILS" }, "he"), /SECRET|DATABASE/);
});
