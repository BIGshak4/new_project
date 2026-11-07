import assert from "node:assert/strict";
import { afterEach, before, mock, test } from "node:test";
import { forgetVisit, readRecentVisits, rememberVisit, type QuestionVisit } from "../src/lib/question-visit-store";

process.env.NEXT_PUBLIC_SUPABASE_URL = "http://localhost:8792";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "local-resume-tests";
let supabase: (typeof import("../src/lib/supabase"))["supabase"];
before(async () => { ({ supabase } = await import("../src/lib/supabase")); });

const restore: (() => void)[] = [];
function installBrowserValue(name: "window" | "localStorage", value: object) {
  const original = Object.getOwnPropertyDescriptor(globalThis, name);
  Object.defineProperty(globalThis, name, { configurable: true, value });
  restore.push(() => {
    if (original) Object.defineProperty(globalThis, name, original);
    else Reflect.deleteProperty(globalThis, name);
  });
}
afterEach(() => {
  mock.restoreAll();
  while (restore.length) restore.pop()!();
});

type Row = { kind: "quick" | "practice"; question_key: string; attempt_id: string | null; visited_at_ms: number; dismissed: boolean };
type Result = { data: Row[] | null; error: { message: string } | null };
const success = (data: Row[] = []): Result => ({ data, error: null });
const offline: Result = { data: null, error: { message: "offline" } };
const quick = (questionKey: string, visitedAt: number): QuestionVisit => ({ kind: "quick", questionKey, visitedAt, attemptId: null });
const questionKeys = (visits: QuestionVisit[]) => visits.map(visit => visit.questionKey);
function deferred<T>() {
  let resolve!: (value: T) => void;
  return { promise: new Promise<T>(yes => { resolve = yes; }), resolve: (value: T) => resolve(value) };
}

function browser(account: string | null) {
  const storage = new Map<string, string>();
  const state = {
    account, quotaExceeded: false,
    writes: [] as { owner: string; events: Row[] }[],
    reads: [] as Map<string, unknown>[],
    write: (_events: Row[]): Promise<Result> => Promise.resolve(success()),
    read: (_filters: Map<string, unknown>): Promise<Result> => Promise.resolve(success()),
  };
  installBrowserValue("window", {});
  installBrowserValue("localStorage", {
    getItem: (key: string) => storage.get(key) ?? null,
    setItem: (key: string, value: string) => {
      if (state.quotaExceeded) throw new Error("Storage quota exceeded");
      storage.set(key, value);
    },
  });
  mock.method(supabase.auth, "getSession", async () => ({
    data: { session: state.account ? { user: { id: state.account } } : null }, error: null,
  }));
  mock.method(supabase, "rpc", (name: string, args: { p_owner: string; p_events: Row[] }) => {
    assert.equal(name, "sync_question_resume_visits");
    return { abortSignal: () => {
      state.writes.push({ owner: args.p_owner, events: args.p_events });
      return state.write(args.p_events);
    } };
  });
  mock.method(supabase, "from", (table: string) => {
    assert.equal(table, "question_resume_visits");
    const filters = new Map<string, unknown>();
    const query = {
      select: () => query, order: () => query, limit: () => query,
      eq: (name: string, value: unknown) => { filters.set(name, value); return query; },
      in: (name: string, values: unknown[]) => { filters.set(name, values); return query; },
      abortSignal: () => { state.reads.push(filters); return state.read(filters); },
    };
    return query;
  });
  return state;
}

test("unavailable sessions keep owner-specific visits locally; a matching account replays only its own events", async () => {
  const state = browser(null);
  await rememberVisit("alice-offline", quick("quick-hw-01", 10));
  await rememberVisit("bob-offline", quick("quick-hw-02", 20));
  assert.deepEqual(questionKeys(await readRecentVisits("alice-offline")), ["quick-hw-01"]);
  state.account = "alice-offline";
  assert.deepEqual(questionKeys(await readRecentVisits("bob-offline")), ["quick-hw-02"]);
  assert.equal(state.reads.length + state.writes.length, 0);
  state.read = async () => success(state.writes.at(-1)!.events);
  assert.deepEqual(questionKeys(await readRecentVisits("alice-offline")), ["quick-hw-01"]);
  await readRecentVisits("alice-offline");
  assert.deepEqual(state.writes.map(write => ({ owner: write.owner, keys: write.events.map(event => event.question_key) })),
    [{ owner: "alice-offline", keys: ["quick-hw-01"] }]);
  assert.ok(state.reads.every(read => read.get("user_id") === "alice-offline"));
});

test("an older write acknowledgment cannot clear a newer failed dismissal's retry", async () => {
  const owner = "overlapping-writes";
  const state = browser(owner);
  const started = deferred<void>(), first = deferred<Result>();
  state.write = async () => { started.resolve(); return first.promise; };
  const writing = rememberVisit(owner, quick("quick-hw-01", 10));
  await started.promise;
  state.write = async () => offline;
  await forgetVisit(owner, quick("quick-hw-01", 20));
  first.resolve(success()); await writing;
  state.write = async () => success();
  assert.deepEqual(await readRecentVisits(owner), []);
  assert.deepEqual(state.writes.map(write => write.events.map(event => [event.visited_at_ms, event.dismissed])),
    [[[10, false]], [[20, true]], [[20, true]]]);
});

test("an old dashboard read cannot resurrect a visit removed by a newer read", async () => {
  const owner = "overlapping-reads";
  const state = browser(owner);
  const visit = quick("quick-hw-01", 10);
  await rememberVisit(owner, visit);
  const oldRows = state.writes[0].events;
  const started = deferred<void>(), delayed = deferred<Result>();
  state.read = async () => { started.resolve(); return delayed.promise; };
  const first = readRecentVisits(owner);
  await started.promise;
  // The other device dismissed the question; this newer snapshot has no active visits.
  state.read = async () => success([]);
  assert.deepEqual(await readRecentVisits(owner), []);
  delayed.resolve(success(oldRows));
  assert.deepEqual(await first, []);
  state.account = null;
  assert.deepEqual(await readRecentVisits(owner), []);
});

test("failure to overwrite a populated local cache still retains the latest offline visit in memory", async () => {
  const owner = "storage-quota";
  const state = browser(null);
  await rememberVisit(owner, quick("quick-hw-01", 10));
  state.quotaExceeded = true;
  await rememberVisit(owner, quick("quick-hw-02", 20));
  assert.deepEqual(questionKeys(await readRecentVisits(owner)), ["quick-hw-02", "quick-hw-01"]);
});

test("a delayed dismissal from an older practice attempt leaves the new attempt available", async () => {
  const owner = "attempts";
  browser(null);
  const previous = { kind: "practice" as const, questionKey: "logic", attemptId: "00000000-0000-4000-8000-000000000001", visitedAt: 10 };
  const current = { ...previous, attemptId: "00000000-0000-4000-8000-000000000002", visitedAt: 20 };
  await rememberVisit(owner, previous);
  await rememberVisit(owner, current);
  await forgetVisit(owner, { ...previous, visitedAt: 30 });
  assert.deepEqual((await readRecentVisits(owner)).map(visit => visit.attemptId), [current.attemptId]);
});

test("a newer remote dismissal suppresses an offline visit even when its write retry fails", async () => {
  const owner = "remote-dismissal";
  const state = browser(null);
  await rememberVisit(owner, quick("quick-hw-01", 10));
  state.account = owner;
  state.write = async () => offline;
  state.read = async filters => {
    if (!filters.get("dismissed")) return success([]);
    assert.deepEqual(filters.get("question_key"), ["quick-hw-01"]);
    return success([{ kind: "quick", question_key: "quick-hw-01", attempt_id: null, visited_at_ms: 20, dismissed: true }]);
  };
  assert.deepEqual(await readRecentVisits(owner), []);
  state.account = null;
  assert.deepEqual(await readRecentVisits(owner), []);
});

test("an offline dismissal for attempt A does not mask another device's open attempt B", async () => {
  const owner = "remote-attempt";
  const state = browser(null);
  const oldId = "00000000-0000-4000-8000-000000000003";
  const currentId = "00000000-0000-4000-8000-000000000004";
  await forgetVisit(owner, { kind: "practice", questionKey: "logic", attemptId: oldId, visitedAt: 30 });
  state.account = owner;
  state.write = async () => offline;
  state.read = async filters => success(filters.get("dismissed") ? [] : [
    { kind: "practice", question_key: "logic", attempt_id: currentId, visited_at_ms: 20, dismissed: false },
  ]);
  assert.deepEqual((await readRecentVisits(owner)).map(visit => visit.attemptId), [currentId]);
});

test("a preview retains an open local draft offline, then leaves the authoritative attempt to the server", async () => {
  const owner = "offline-preview";
  const state = browser(null);
  const attemptId = "00000000-0000-4000-8000-000000000005";
  const question = { kind: "practice" as const, questionKey: "logic", attemptId, visitedAt: 10 };
  await rememberVisit(owner, question);
  await rememberVisit(owner, { ...question, visitedAt: 20, attemptId: null });
  const offlineVisits = await readRecentVisits(owner);
  assert.deepEqual(offlineVisits.map(visit => [visit.visitedAt, visit.attemptId]), [[20, attemptId]]);
  state.account = owner;
  state.read = async () => success([
    { kind: "practice", question_key: "logic", attempt_id: attemptId, visited_at_ms: 20, dismissed: false },
  ]);
  assert.deepEqual((await readRecentVisits(owner)).map(visit => visit.attemptId), [attemptId]);
  assert.equal(state.writes.length, 1);
  assert.equal(state.writes[0].events[0].attempt_id, null);
});

test("a malformed stored timestamp or attempt ID cannot poison replay of valid visits", async () => {
  const owner = "invalid-cache";
  const state = browser(owner);
  const entry = { kind: "practice", questionKey: "logic", visitedAt: 10, attemptId: null, dismissed: false, pending: true };
  localStorage.setItem(`jobrun-resume-visits-v1:${owner}`, JSON.stringify([
    { ...entry, questionKey: "bad-id", attemptId: "invalid uuid" },
    { ...entry, questionKey: "future", visitedAt: Number.MAX_SAFE_INTEGER },
    entry,
  ]));
  state.read = async () => success(state.writes[0].events);
  assert.deepEqual(questionKeys(await readRecentVisits(owner)), ["logic"]);
  assert.deepEqual(state.writes[0].events.map(event => event.question_key), ["logic"]);
});
