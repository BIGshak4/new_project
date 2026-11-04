import assert from "node:assert/strict";
import { afterEach, before, mock, test } from "node:test";
import type { Entry } from "../src/lib/practice-ui";

process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "test-publishable-key";
let bookmarks: typeof import("../src/lib/question-bookmark");
let db: (typeof import("../src/lib/supabase"))["supabase"];
before(async () => {
  bookmarks = await import("../src/lib/question-bookmark");
  db = (await import("../src/lib/supabase")).supabase;
});
afterEach(() => mock.restoreAll());

const columns = "id,user_id,question_id,answer,self_rating,bookmarked,completed,hidden,version";
const entry = (patch: Partial<Entry> = {}): Entry => ({
  id: "entry-question", user_id: "owner", question_id: "question", answer: "my saved draft",
  self_rating: 2, bookmarked: true, completed: true, hidden: true, version: 4, ...patch,
});
type Response = { data: Entry | null; error: { code?: string; message: string } | null };
type Write = {
  table: string;
  kind?: "update" | "insert";
  payload?: Record<string, unknown>;
  filters: Record<string, unknown>;
  columns?: string;
};

function captureWrites(responses: Response[]) {
  const writes: Write[] = [];
  const pending = [...responses];
  const from = (table: string) => {
    const write: Write = { table, filters: {} };
    writes.push(write);
    const finish = async () => {
      const response = pending.shift();
      assert.ok(response, "Unexpected additional persistence request");
      return response;
    };
    const query = {
      update(payload: Record<string, unknown>) { write.kind = "update"; write.payload = payload; return query; },
      insert(payload: Record<string, unknown>) { write.kind = "insert"; write.payload = payload; return query; },
      eq(column: string, value: unknown) { write.filters[column] = value; return query; },
      select(selected: string) { write.columns = selected; return query; },
      maybeSingle: finish,
      single: finish,
    };
    return query;
  };
  mock.method(db, "from", from as unknown as typeof db.from);
  return writes;
}

test("bookmark updates patch only the bookmark and retain notes, ratings and other flags", async () => {
  const saved = entry({ bookmarked: false });
  const writes = captureWrites([{ data: saved, error: null }]);
  assert.deepEqual(await bookmarks.saveQuestionBookmark("owner", "question", false), saved);
  assert.deepEqual(writes[0], {
    table: "jr_practice_entries", kind: "update", payload: { bookmarked: false },
    filters: { user_id: "owner", question_id: "question" }, columns,
  });
});

test("the first bookmark inserts only its identity and bookmark flag", async () => {
  const saved = entry({ answer: "", self_rating: null, completed: false, hidden: false, version: 1 });
  const writes = captureWrites([{ data: null, error: null }, { data: saved, error: null }]);
  assert.deepEqual(await bookmarks.saveQuestionBookmark("owner", "question", true), saved);
  const insertion = writes.find(write => write.kind === "insert");
  assert.deepEqual(insertion, {
    table: "jr_practice_entries", kind: "insert",
    payload: { user_id: "owner", question_id: "question", bookmarked: true },
    filters: {}, columns,
  });
});

test("a concurrent first-save conflict retries a partial update without overwriting new notes", async () => {
  const saved = entry({ answer: "draft saved by another tab", version: 7 });
  const writes = captureWrites([
    { data: null, error: null },
    { data: null, error: { code: "23505", message: "duplicate key" } },
    { data: saved, error: null },
  ]);
  assert.deepEqual(await bookmarks.saveQuestionBookmark("owner", "question", true), saved);
  assert.deepEqual(writes.map(write => write.kind), ["update", "insert", "update"]);
  assert.deepEqual(writes[2].payload, { bookmarked: true });
  assert.deepEqual(writes[2].filters, { user_id: "owner", question_id: "question" });
});

test("database failures and unsuccessful retry responses never look saved", async (context) => {
  const denied = { code: "42501", message: "permission denied" };
  for (const [name, responses] of [
    ["update denied", [{ data: null, error: denied }]],
    ["insert denied", [{ data: null, error: null }, { data: null, error: denied }]],
    ["insert returned no record", [{ data: null, error: null }, { data: null, error: null }]],
    ["conflict retry returned no record", [{ data: null, error: null }, { data: null, error: { code: "23505", message: "duplicate key" } }, { data: null, error: null }]],
  ] as [string, Response[]][]) {
    await context.test(name, async () => {
      captureWrites(responses);
      await assert.rejects(bookmarks.saveQuestionBookmark("owner", "question", true));
      mock.restoreAll();
    });
  }
});

test("foreign-account, wrong-question and mismatched bookmark responses are rejected", async (context) => {
  for (const [name, patch] of [
    ["foreign account", { user_id: "other-account" }],
    ["wrong question", { question_id: "other-question" }],
    ["bookmark did not change", { bookmarked: false }],
  ] as [string, Partial<Entry>][]) {
    await context.test(name, async () => {
      captureWrites([{ data: entry(patch), error: null }]);
      await assert.rejects(bookmarks.saveQuestionBookmark("owner", "question", true));
      mock.restoreAll();
    });
  }
});
