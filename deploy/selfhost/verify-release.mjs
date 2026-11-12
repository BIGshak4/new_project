import { pathToFileURL } from "node:url";

function healthUrl(origin, path) {
  const url = new URL(origin);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password
      || url.pathname !== "/" || url.search || url.hash) {
    throw new Error("Supply an HTTP(S) origin without credentials, a path, query or fragment");
  }
  return new URL(path, url).href;
}

/** Check both halves of a coordinated release; never print the full health response. */
export async function verifyRelease({ revision, app, api, tasks, fetchHealth = fetch }) {
  if (!/^[0-9a-f]{40}$/.test(revision ?? "")) {
    throw new Error("The expected revision must be the full 40-character lowercase Git SHA");
  }
  const checks = [
    { name: "web", url: healthUrl(app, "/api/health"), field: "revision" },
    { name: "api", url: healthUrl(api, "/health"), field: "source_revision" },
  ];
  if (tasks) checks.push({ name: "tasks", url: healthUrl(tasks, "/api/health"), field: "revision" });
  return Promise.all(checks.map(async ({ name, url, field }) => {
    const response = await fetchHealth(url, { redirect: "error", signal: AbortSignal.timeout(15_000) });
    if (!response.ok) throw new Error(`${name}: HTTP ${response.status}`);
    let health;
    try {
      health = await response.json();
    } catch {
      throw new Error(`${name}: health endpoint did not return JSON`);
    }
    if (health.status !== "ok" || health[field] !== revision) {
      throw new Error(`${name}: healthy expected revision is not live`);
    }
    return { service: name, revision };
  }));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [revision, app, api, tasks] = process.argv.slice(2);
  try {
    if (!app || !api) throw new Error("Usage: node verify-release.mjs FULL_SHA APP_ORIGIN API_ORIGIN [TASKS_ORIGIN]");
    const results = await verifyRelease({ revision, app, api, tasks });
    for (const result of results) console.log(`${result.service}: ok ${result.revision}`);
  } catch (error) {
    console.error(error instanceof Error ? error.message : "Release verification failed");
    process.exitCode = 1;
  }
}
