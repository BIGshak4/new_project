import assert from "node:assert/strict";
import { test } from "node:test";
import { AccessCheck, accessForUser, type AccessState } from "../src/lib/auth-access";

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((yes) => { resolve = yes; });
  return { promise, resolve };
}

test("a stalled membership request leaves the loading gate after 15 seconds and fails closed", async (context) => {
  context.mock.timers.enable({ apis: ["setTimeout"] });
  const request = deferred<boolean>();
  const states: AccessState[] = [];
  let signal!: AbortSignal;
  const checking = new AccessCheck().run("user", (nextSignal) => {
    signal = nextSignal;
    return request.promise;
  }, () => "user", (state) => states.push(state));

  context.mock.timers.tick(14_999);
  assert.deepEqual(accessForUser("user", states.at(-1)!), { checking: true, allowed: false, failed: false });
  context.mock.timers.tick(1);
  await checking;
  assert.equal(signal.aborted, true);
  assert.deepEqual(accessForUser("user", states.at(-1)!), { checking: false, allowed: false, failed: true });

  request.resolve(true);
  await request.promise;
  assert.equal(states.some((state) => state.allowed), false, "a grant arriving after the deadline must stay ignored");
});

test("retry after a membership timeout can succeed without being cancelled later", async (context) => {
  context.mock.timers.enable({ apis: ["setTimeout"] });
  const states: AccessState[] = [];
  const access = new AccessCheck();
  const stalled = access.run("user", () => new Promise<boolean>(() => {}), () => "user", (state) => states.push(state));
  context.mock.timers.tick(15_000);
  await stalled;
  let retrySignal!: AbortSignal;
  await access.run("user", async (signal) => { retrySignal = signal; return true; }, () => "user", (state) => states.push(state));
  context.mock.timers.tick(30_000);

  assert.equal(retrySignal.aborted, false);
  assert.deepEqual(accessForUser("user", states.at(-1)!), { checking: false, allowed: true, failed: false });
});

test("an old account's membership timeout cannot overwrite the new account's access", async (context) => {
  context.mock.timers.enable({ apis: ["setTimeout"] });
  const states: AccessState[] = [];
  const access = new AccessCheck();
  let currentUser = "old";
  const old = access.run("old", () => new Promise<boolean>(() => {}), () => currentUser, (state) => states.push(state));
  currentUser = "new";
  await access.run("new", async () => true, () => currentUser, (state) => states.push(state));
  context.mock.timers.tick(15_000);
  await old;

  assert.deepEqual(states.at(-1), { userId: "new", checking: false, allowed: true, failed: false });
  assert.equal(states.filter((state) => state.userId === "old").length, 1);
});

test("a transport cannot turn deadline cancellation into a membership grant", async (context) => {
  context.mock.timers.enable({ apis: ["setTimeout"] });
  const states: AccessState[] = [];
  const checking = new AccessCheck().run("user", (signal) => new Promise<boolean>((resolve) => {
    signal.addEventListener("abort", () => resolve(true), { once: true });
  }), () => "user", (state) => states.push(state));
  context.mock.timers.tick(15_000);
  await checking;

  assert.deepEqual(states.at(-1), { userId: "user", checking: false, allowed: false, failed: true });
});
