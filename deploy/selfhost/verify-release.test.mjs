import assert from "node:assert/strict";
import { test } from "node:test";
import { verifyRelease } from "./verify-release.mjs";

const revision = "a".repeat(40);
const origins = { app: "https://example.com", api: "https://api.example.com" };
const response = (body, status = 200) => new Response(JSON.stringify(body), { status });

test("requires matching healthy frontend and backend revisions, including optional tasks", async () => {
  const requests = [];
  const results = await verifyRelease({ revision, ...origins, tasks: "https://tasks.example.com", fetchHealth: async (url, options) => {
    requests.push({ url, redirect: options.redirect, signal: options.signal });
    return response({ status: "ok", revision, source_revision: revision });
  } });
  assert.deepEqual(results.map(({ service }) => service), ["web", "api", "tasks"]);
  assert.deepEqual(requests.map(({ url }) => url), ["https://example.com/api/health", "https://api.example.com/health", "https://tasks.example.com/api/health"]);
  assert.ok(requests.every(({ redirect, signal }) => redirect === "error" && signal instanceof AbortSignal));
});

test("rejects mixed release versions even when both services return 200", async () => {
  await assert.rejects(verifyRelease({ revision, ...origins, fetchHealth: async (url) => response({
    status: "ok", revision, source_revision: url.includes("api.example.com") ? "b".repeat(40) : revision,
  }) }), /api: healthy expected revision is not live/);
});

test("rejects unavailable or unhealthy services", async () => {
  await assert.rejects(verifyRelease({ revision, ...origins, fetchHealth: async () => response({}, 503) }), /HTTP 503/);
  await assert.rejects(verifyRelease({ revision, ...origins, fetchHealth: async () => response({ status: "degraded", revision, source_revision: revision }) }), /healthy expected revision/);
  await assert.rejects(verifyRelease({ revision, ...origins, fetchHealth: async () => new Response("not JSON") }), /health endpoint did not return JSON/);
});

test("rejects a short SHA or ambiguous origin before sending requests", async () => {
  const neverFetch = async () => { throw new Error("must not fetch"); };
  await assert.rejects(verifyRelease({ revision: "abc123", ...origins, fetchHealth: neverFetch }), /full 40-character/);
  await assert.rejects(verifyRelease({ revision, ...origins, app: "https://example.com/path", fetchHealth: neverFetch }), /Supply an HTTP/);
  await assert.rejects(verifyRelease({ revision, ...origins, app: "https://user:secret@example.com", fetchHealth: neverFetch }), /Supply an HTTP/);
});
