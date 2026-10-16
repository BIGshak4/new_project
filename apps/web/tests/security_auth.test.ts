import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import ts from "typescript";
import * as practiceAuth from "../src/lib/auth-access";
import * as taskAuth from "../../tasks/src/lib/auth-access";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

for (const [name, implementation] of [["practice", practiceAuth], ["tasks", taskAuth]] as const) {
  function authHarness() {
    const initial = deferred<{ data: { user: { id: string } | null } }>();
    let callback!: (event: string, session: { user: { id: string } } | null) => void;
    let unsubscribed = false;
    const published: Array<{ id: string } | null> = [];
    const stop = implementation.observeAuthUser({
      getUser: () => initial.promise,
      onAuthStateChange: (onChange) => {
        callback = onChange;
        return { data: { subscription: { unsubscribe() { unsubscribed = true; } } } };
      },
    }, (user) => published.push(user));
    return { initial, published, stop, emit: (user: { id: string } | null) => callback("change", user && { user }), unsubscribed: () => unsubscribed };
  }

  test(`${name}: delayed initial getUser cannot restore an account after sign-out`, async () => {
    const h = authHarness();
    h.emit(null);
    h.initial.resolve({ data: { user: { id: "old-account" } } });
    await h.initial.promise;
    assert.deepEqual(h.published, [null]);
    h.stop();
  });

  test(`${name}: delayed initial getUser or its failure cannot overwrite a later account`, async () => {
    for (const rejected of [false, true]) {
      const h = authHarness();
      h.emit({ id: "new-account" });
      if (rejected) h.initial.reject(new Error("old request failed"));
      else h.initial.resolve({ data: { user: { id: "old-account" } } });
      await h.initial.promise.catch(() => undefined);
      assert.deepEqual(h.published, [{ id: "new-account" }]);
      h.stop();
    }
  });

  test(`${name}: initial identity works and cleanup suppresses queued auth callbacks`, async () => {
    const h = authHarness();
    h.initial.resolve({ data: { user: { id: "current" } } });
    await h.initial.promise;
    assert.deepEqual(h.published, [{ id: "current" }]);
    h.stop();
    h.emit({ id: "queued-after-unmount" });
    assert.deepEqual(h.published, [{ id: "current" }]);
    assert.equal(h.unsubscribed(), true);
  });

  test(`${name}: failed initial verification exposes no authenticated workspace`, async () => {
    const h = authHarness();
    h.initial.reject(new Error("offline"));
    await h.initial.promise.catch(() => undefined);
    assert.deepEqual(h.published, [null]);
    h.stop();
  });

  test(`${name}: a previous user's grant cannot authorize the new user, even before effects run`, () => {
    const grant = { userId: "first", allowed: true, checking: false, failed: false };
    assert.deepEqual(implementation.accessForUser("first", grant), { checking: false, allowed: true, failed: false });
    assert.deepEqual(implementation.accessForUser("second", grant), { checking: true, allowed: false, failed: false });
    assert.deepEqual(implementation.accessForUser(undefined, grant), { checking: false, allowed: false, failed: false });
    assert.deepEqual(implementation.accessForUser("second", null), { checking: true, allowed: false, failed: false });
  });

  test(`${name}: a late membership grant after switching accounts is ignored`, async () => {
    const pending = deferred<boolean>();
    const access = new implementation.AccessCheck();
    const states: practiceAuth.AccessState[] = [];
    let current = "first";
    const old = access.run("first", () => pending.promise, () => current, (state) => states.push(state));
    current = "second";
    await access.run("second", async () => false, () => current, (state) => states.push(state));
    pending.resolve(true);
    await old;
    assert.deepEqual(states.at(-1), { userId: "second", checking: false, allowed: false, failed: false });
    assert.equal(states.some((state) => state.userId === "first" && state.allowed), false);
  });

  test(`${name}: a newer denial cannot be overwritten by an older grant for the same account`, async () => {
    const pending = deferred<boolean>();
    const access = new implementation.AccessCheck();
    const states: practiceAuth.AccessState[] = [];
    const old = access.run("user", () => pending.promise, () => "user", (state) => states.push(state));
    await access.run("user", async () => false, () => "user", (state) => states.push(state));
    pending.resolve(true);
    await old;
    assert.equal(states.at(-1)?.allowed, false);
    assert.equal(states.some((state) => state.allowed), false);
  });

  test(`${name}: unmount invalidates pending checks and retry remains possible`, async () => {
    const pending = deferred<boolean>();
    const access = new implementation.AccessCheck();
    const states: practiceAuth.AccessState[] = [];
    const old = access.run("user", () => pending.promise, () => "user", (state) => states.push(state));
    access.invalidate();
    pending.resolve(true);
    await old;
    assert.equal(states.length, 1);
    await access.run("user", async () => { throw new Error("query failed"); }, () => "user", (state) => states.push(state));
    assert.deepEqual(states.at(-1), { userId: "user", checking: false, allowed: false, failed: true });
    await access.run("user", async () => true, () => "user", (state) => states.push(state));
    assert.deepEqual(states.at(-1), { userId: "user", checking: false, allowed: true, failed: false });
  });

  test(`${name}: an obsolete component cannot start an access check for a different account`, async () => {
    const access = new implementation.AccessCheck();
    let queried = false;
    await access.run("old", async () => { queried = true; return true; }, () => "new", () => assert.fail("published stale access"));
    assert.equal(queried, false);
  });

  // Integration policy guard: check the production form, not a second copy of its submission logic.
  test(`${name}: the real form clears its controlled password before awaiting authentication`, () => {
    const path = name === "practice" ? "../src/components/auth.tsx" : "../../tasks/src/components/auth.tsx";
    const source = ts.createSourceFile(path, readFileSync(new URL(path, import.meta.url), "utf8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    let submit: ts.FunctionDeclaration | undefined;
    function visit(node: ts.Node) {
      if (ts.isFunctionDeclaration(node) && node.name?.text === "submit") submit = node;
      ts.forEachChild(node, visit);
    }
    visit(source);
    assert.ok(submit?.body);
    const clear = submit.body.statements.findIndex((statement) => ts.isExpressionStatement(statement) && ts.isCallExpression(statement.expression)
      && statement.expression.expression.getText(source) === "setPassword" && statement.expression.arguments[0]?.getText(source) === '""');
    const request = submit.body.statements.findIndex((statement) => ts.isTryStatement(statement));
    assert.ok(clear >= 0 && clear < request, "password must be removed from React state before the request settles");
  });
}
