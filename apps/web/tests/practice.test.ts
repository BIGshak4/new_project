import assert from "node:assert/strict";
import { afterEach, before, mock, test } from "node:test";
import type { Attempt, Submission } from "../src/lib/practice-api";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "test-publishable-key";
let client: typeof import("../src/lib/practice-api");
let ui: typeof import("../src/lib/practice-ui");
let supabase: (typeof import("../src/lib/supabase"))["supabase"];
before(async () => {
  client = await import("../src/lib/practice-api");
  ui = await import("../src/lib/practice-ui");
  ({ supabase } = await import("../src/lib/supabase"));
});
afterEach(() => mock.restoreAll());

test("a late language-refresh snapshot cannot undo a newly saved bookmark", () => {
  const entry = {
    id: "e",
    user_id: "u",
    question_id: "q",
    answer: "",
    self_rating: null,
    bookmarked: true,
    completed: false,
    version: 2,
  };
  assert.equal(ui.mergeEntries([entry], [])[0].bookmarked, true);
  assert.equal(
    ui.mergeEntries([entry], [{ ...entry, bookmarked: false, version: 1 }])[0]
      .bookmarked,
    true,
  );
  assert.equal(
    ui.mergeEntries([entry], [{ ...entry, bookmarked: false, version: 3 }])[0]
      .bookmarked,
    false,
  );
});
function signedIn() {
  mock.method(supabase.auth, "getSession", async () => ({
    data: { session: { access_token: "test-access" } },
    error: null,
  }));
}
function capture(response: Response) {
  const requests: { url: string; init: RequestInit }[] = [];
  mock.method(globalThis, "fetch", async (url: string, init: RequestInit) => {
    requests.push({ url, init });
    return response;
  });
  return requests;
}
const attempt = (
  main: Partial<Submission> | null,
  follow: Partial<Submission>[] = [],
) =>
  ({
    submission: main,
    follow_ups: follow.map((submission) => ({ submission })),
  }) as Attempt;

test("main submission carries bearer auth, original text, and a stable idempotency key", async () => {
  signedIn();
  const calls = capture(Response.json({ submission: {}, attempt: {} }));
  await client
    .practiceApi("https://api.example/")
    .submit("attempt-1", { text: "הסבר\ncode", revision_count: 2 }, "same-key");
  assert.equal(calls.length, 1);
  assert.equal(
    calls[0].url,
    "https://api.example/v1/practice/attempts/attempt-1/submissions",
  );
  assert.deepEqual(JSON.parse(calls[0].init.body as string), {
    answer: { text: "הסבר\ncode" },
    revision_count: 2,
  });
  assert.equal(
    (calls[0].init.headers as Record<string, string>).Authorization,
    "Bearer test-access",
  );
  assert.equal(
    (calls[0].init.headers as Record<string, string>)["Idempotency-Key"],
    "same-key",
  );
  assert.equal(calls[0].init.cache, "no-store");
  assert.ok(calls[0].init.signal instanceof AbortSignal);
});

test("a lost response is not automatically posted a second time", async () => {
  signedIn();
  const fetch = mock.method(globalThis, "fetch", async () => {
    throw new TypeError("connection reset");
  });
  await assert.rejects(
    client
      .practiceApi("https://api.example")
      .submit("a", { text: "answer" }, "k"),
    (e: unknown) =>
      e instanceof client.PracticeApiError && e.code === "network",
  );
  assert.equal(fetch.mock.callCount(), 1);
});

test("202 preserves evaluating status so the UI can observe the saved attempt", async () => {
  signedIn();
  capture(
    Response.json(
      {
        submission: { status: "evaluating" },
        attempt: { id: "a", status: "evaluating" },
      },
      { status: 202 },
    ),
  );
  const result = await client
    .practiceApi("https://api.example")
    .submit("a", { text: "answer" }, "k");
  assert.equal(result.attempt.status, "evaluating");
});

test("stable API errors retain their status and request id", async () => {
  signedIn();
  capture(
    Response.json(
      { error: { code: "usage_limit", message: "daily limit" } },
      { status: 429, headers: { "x-request-id": "trace-1" } },
    ),
  );
  await assert.rejects(
    client
      .practiceApi("https://api.example")
      .startAttempt({ question_key: "q" }),
    (e: unknown) =>
      e instanceof client.PracticeApiError &&
      e.code === "usage_limit" &&
      e.status === 429 &&
      e.requestId === "trace-1",
  );
});

test("an absent session prevents any API request", async () => {
  mock.method(supabase.auth, "getSession", async () => ({
    data: { session: null },
    error: null,
  }));
  const calls = capture(Response.json({}));
  await assert.rejects(
    client.practiceApi("https://api.example").progress(),
    (e: unknown) =>
      e instanceof client.PracticeApiError && e.code === "unauthenticated",
  );
  assert.equal(calls.length, 0);
});

test("resume is a GET; follow-up submission targets the supplied turn", async () => {
  signedIn();
  const calls = capture(Response.json({}));
  await client.practiceApi("https://api.example").getAttempt("a");
  assert.equal(calls[0].init.method, "GET");
  mock.restoreAll();
  signedIn();
  const follow = capture(Response.json({}));
  await client
    .practiceApi("https://api.example")
    .submitFollowUp("a", 2, { text: "follow up" }, "k2");
  assert.equal(
    follow[0].url,
    "https://api.example/v1/practice/attempts/a/follow-ups/2/submissions",
  );
  assert.equal(
    (follow[0].init.headers as Record<string, string>)["Idempotency-Key"],
    "k2",
  );
});

test("recovery resolves a lost response and an answer accepted from another tab", () => {
  const p = { key: "k", turn: null, text: "answer" };
  assert.equal(ui.pendingResolved(attempt(null), p), false);
  assert.equal(ui.pendingResolved(attempt({ key: "k", turn: 0 }), p), true);
  assert.equal(
    ui.pendingResolved(attempt({ key: "other-tab", turn: 0 }), p),
    true,
  );
  assert.equal(
    ui.pendingResolved(attempt({ key: "main", turn: 0 }), { ...p, turn: 1 }),
    false,
  );
  assert.equal(
    ui.pendingResolved(attempt(null, [{ key: "k", turn: 1 }]), {
      ...p,
      turn: 1,
    }),
    true,
  );
});

test("retry chooses the newest saved revision, including a failed follow-up", () => {
  const a = attempt({ revision: 1, status: "done" }, [
    { revision: 3, status: "failed" },
    { revision: 2, status: "done" },
  ]);
  assert.equal(ui.latestSubmission(a)?.revision, 3);
  assert.equal(ui.latestSubmission(a)?.status, "failed");
});
