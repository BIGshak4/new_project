import assert from "node:assert/strict";
import test from "node:test";
import { InboxRefresh, InboxRequests, supportStatus, userInboxApi, type InboxRpc } from "../src/lib/user-inbox";

test("a response cannot reach an account after sign-out, replacement login or returning to the original account", () => {
  const requests = new InboxRequests();
  requests.bind("learner-a");
  const previous = requests.start("badge");
  assert.equal(previous(), true);
  requests.bind(null);
  assert.equal(previous(), false);
  assert.equal(requests.start("badge")(), false);
  requests.bind("learner-b");
  const second = requests.start("content");
  requests.bind("learner-a");
  assert.equal(previous(), false);
  assert.equal(second(), false);
});

test("newer refreshes supersede stale responses without canceling independent download/read channels", () => {
  const requests = new InboxRequests(); requests.bind("learner-a");
  const older = requests.start("content");
  const read = requests.start("read:message-one");
  const newer = requests.start("content");
  assert.equal(older(), false); assert.equal(newer(), true); assert.equal(read(), true);
  requests.invalidate();
  assert.equal(newer(), false); assert.equal(read(), false);
});

test("binding the same authenticated account preserves pending requests across token refresh", () => {
  const requests = new InboxRequests(); requests.bind("learner-a");
  const current = requests.start("content"); requests.bind("learner-a");
  assert.equal(current(), true);
});

test("a delayed read acknowledgement refreshes the newly opened report rather than superseding it with the previous report", async () => {
  const requests = new InboxRequests(); requests.bind("learner-a");
  const refresh = new InboxRefresh();
  const loads: string[] = [];
  refresh.set(async () => { loads.push("report-a"); requests.start("content"); });
  let acknowledge!: () => void;
  const response = new Promise<void>(resolve => { acknowledge = resolve; });
  const currentRead = requests.start("read:report-a-update");
  const followUp = response.then(async () => { if (currentRead()) await refresh.run(); });
  const navigationToB = requests.start("content");
  refresh.set(async () => { loads.push("report-b"); });
  acknowledge(); await followUp;
  assert.deepEqual(loads, ["report-b"]);
  assert.equal(navigationToB(), true, "a stale report A reload must not supersede report B's content request");
});

test("delayed mark-all follows the current tab while an account switch cancels its follow-up entirely", async () => {
  const requests = new InboxRequests(); requests.bind("learner-a");
  const refresh = new InboxRefresh(); const loads: string[] = [];
  refresh.set(async () => { loads.push("updates"); });
  let acknowledge!: () => void;
  const response = new Promise<void>(resolve => { acknowledge = resolve; });
  const currentWrite = requests.start("mark-all");
  const followUp = response.then(async () => { if (currentWrite()) await refresh.run(); });
  refresh.set(async () => { loads.push("my-requests"); });
  acknowledge(); await followUp;
  assert.deepEqual(loads, ["my-requests"]);
  const oldAccountWrite = requests.start("mark-all");
  requests.bind("learner-b");
  if (oldAccountWrite()) await refresh.run();
  assert.deepEqual(loads, ["my-requests"]);
});

test("inbox feed requests the chosen language and bounded pagination without implying read state", async () => {
  const calls: Array<{ name: string; args?: Record<string, unknown> }> = [];
  const api = userInboxApi(async (name, args) => { calls.push({ name, args }); return { data: { items: [], total: 0, unread_count: 3 }, error: null }; });
  const feed = await api.feed("en", "announcement", 2);
  assert.equal(feed.unread_count, 3);
  assert.deepEqual(calls, [{ name: "jr_user_inbox", args: { p_kind: "announcement", p_page: 2, p_page_size: 20, p_language: "en" } }]);
});

test("read acknowledgement must belong to the viewed item and use the server's timestamp", async () => {
  const expected = { kind: "announcement" as const, id: "update-one" };
  const timestamp = "2026-10-20T10:00:00Z";
  const api = userInboxApi(async (name, args) => {
    assert.equal(name, "jr_mark_inbox_read");
    assert.deepEqual(args, { p_kind: expected.kind, p_id: expected.id });
    return { data: { ...expected, read_at: timestamp }, error: null };
  });
  assert.equal(await api.markRead(expected), timestamp);
  for (const invalid of [{ ...expected, id: "different-message", read_at: timestamp }, { ...expected, read_at: null }]) {
    const bad = userInboxApi(async () => ({ data: invalid, error: null }));
    await assert.rejects(() => bad.markRead(expected), /not confirmed/);
  }
});

test("mark-all uses one server transaction without a client cutoff or optimistic zero unread count", async () => {
  const calls: Array<{ name: string; args?: Record<string, unknown> }> = [];
  const api = userInboxApi(async (name, args) => { calls.push({ name, args }); return { data: { marked: 7 }, error: null }; });
  assert.equal(await api.markAllRead(), 7);
  assert.deepEqual(calls, [{ name: "jr_mark_all_inbox_read", args: undefined }]);
});

test("support details and pagination remain owner-scoped server RPCs with no user/admin identifier supplied", async () => {
  const calls: Array<{ name: string; args?: Record<string, unknown> }> = [];
  const rpc: InboxRpc = async (name, args) => {
    calls.push({ name, args });
    return { data: name === "jr_my_support_reports" ? { reports: [], total: 0 } : { report: { id: "own-report" }, files: [], updates: [] }, error: null };
  };
  const api = userInboxApi(rpc); await api.reports(3); await api.detail("own-report");
  assert.deepEqual(calls, [
    { name: "jr_my_support_reports", args: { p_page: 3, p_page_size: 20 } },
    { name: "jr_my_support_detail", args: { p_id: "own-report" } },
  ]);
});

test("unavailable inbox data or failed read writes never masquerade as successful empty/read states", async () => {
  const error = new Error("not authorized");
  const rejected = userInboxApi(async () => ({ data: null, error }));
  await assert.rejects(() => rejected.feed("he"), error);
  await assert.rejects(() => rejected.markAllRead(), error);
  for (const data of [null, { items: [], total: -1, unread_count: 0 }, { items: [], total: 0, unread_count: "0" }]) {
    await assert.rejects(() => userInboxApi(async () => ({ data, error: null })).feed("he"));
  }
});

test("support statuses display bilingual user-facing states and handle unknown future values safely", () => {
  assert.equal(supportStatus("in_progress", true), "בטיפול");
  assert.equal(supportStatus("resolved", false), "Resolved");
  assert.equal(supportStatus("closed", true), "נסגרה");
  assert.equal(supportStatus("new-future-status", false), "Under review");
});
