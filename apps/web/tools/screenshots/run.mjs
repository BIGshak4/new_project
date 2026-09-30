// Photographs every screen of the JobRun web app, signed in, at phone and desktop width, in Hebrew and English,
// without a real Supabase account: a local API with instant scripted grading (backend/scripts/screenshot_server.py),
// a stand-in for the Supabase endpoints the browser calls, the Next dev server, and headless Edge driven over the
// DevTools protocol (headless windows cannot be narrower than ~500 px, so the phone size uses device emulation).
//
//   npm run screenshots                       # -> %TEMP%\jobrun-shots (or --out <dir>)
//   node tools/screenshots/run.mjs --out C:\shots --langs he --widths 390
//
// Output: <screen>-<lang>-<width>.png and index.json (per shot: innerWidth vs scrollWidth, console errors).
// Nothing here touches production code paths; the session is injected into localStorage the way supabase-js stores it.

import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync, existsSync, rmSync } from "node:fs";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const webDir = resolve(here, "..", "..");
const backendDir = resolve(webDir, "..", "..", "backend");
const args = Object.fromEntries(process.argv.slice(2).map((a, i, all) => (a.startsWith("--") ? [a.slice(2), all[i + 1] ?? "1"] : [])).filter((x) => x.length));
const OUT = resolve(args.out ?? join(tmpdir(), "jobrun-shots"));
const LANGS = (args.langs ?? "he,en").split(",");
const WIDTHS = (args.widths ?? "1280,390").split(",").map(Number);
// free ports by default: a server left over from an earlier run must never answer this run's health checks
const freePort = () => new Promise((r) => { const s = createServer(); s.listen(0, "127.0.0.1", () => { const { port } = s.address(); s.close(() => r(port)); }); });
const API_PORT = Number(args["api-port"] ?? (await freePort())), STUB_PORT = Number(args["stub-port"] ?? (await freePort())), WEB_PORT = Number(args["web-port"] ?? (await freePort()));
const EDGE = process.env.EDGE_PATH ?? "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const procs = [];
const started = Date.now();
const log = (...m) => console.log(`[${((Date.now() - started) / 1000).toFixed(0)}s]`, ...m);

function start(cmd, argv, opts) {
  const p = spawn(cmd, argv, { stdio: ["ignore", "pipe", "pipe"], ...opts });
  p.stdout.on("data", (d) => { if (args.verbose) process.stdout.write(`  ${opts.name}: ${d}`); });
  p.stderr.on("data", (d) => { if (args.verbose) process.stdout.write(`  ${opts.name}! ${d}`); });   // the browser aborting a connection is noise
  procs.push(p);
  return p;
}
async function waitFor(url, seconds = 120, ok = (r) => r.ok) {
  const deadline = Date.now() + seconds * 1000;
  while (Date.now() < deadline) {
    try { const r = await fetch(url); if (ok(r)) return; } catch {}
    await sleep(500);
  }
  throw new Error(`not ready: ${url}`);
}
function stopAll() {
  for (const p of procs) { try { process.platform === "win32" ? spawnSync("taskkill", ["/pid", String(p.pid), "/T", "/F"], { stdio: "ignore" }) : p.kill(); } catch {} }
  if (process.platform === "win32") {            // children started through a shell can outlive it: kill by port too
    const ports = [API_PORT, STUB_PORT, WEB_PORT].join(",");
    spawnSync("powershell", ["-NoProfile", "-Command", `Get-NetTCPConnection -LocalPort ${ports} -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }`], { stdio: "ignore" });
  }
}
process.on("exit", stopAll);
process.on("SIGINT", () => { stopAll(); process.exit(1); });

// ------------------------------------------------------------------------------------------ backend + seed data

mkdirSync(OUT, { recursive: true });
const sessionFile = join(OUT, "session.json");
if (existsSync(sessionFile)) rmSync(sessionFile);
start("uv", ["run", "python", "scripts/screenshot_server.py", "--api-port", String(API_PORT), "--stub-port", String(STUB_PORT), "--session-file", sessionFile,
  "--web-origin", `http://localhost:${WEB_PORT}`], { cwd: backendDir, name: "backend", shell: true });
await waitFor(`http://127.0.0.1:${API_PORT}/health`);
await waitFor(`http://127.0.0.1:${STUB_PORT}/health`);
for (let i = 0; i < 60 && !existsSync(sessionFile); i++) await sleep(250);
if (!existsSync(sessionFile)) throw new Error("the backend did not write the session file; is another server on its ports?");
const { session, api } = JSON.parse(readFileSync(sessionFile, "utf-8"));
log("backend up");

const call = async (method, path, body, lang = "he") => {
  const r = await fetch(api + path, {
    method,
    headers: { Authorization: `Bearer ${session.access_token}`, "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${method} ${path} -> ${r.status} ${await r.text()}`);
  return r.json();
};
async function waitWords(attemptId) {
  for (let i = 0; i < 60; i++) {
    const a = await call("GET", `/v1/practice/attempts/${attemptId}`);
    const pending = a.feedback_pending || a.status === "evaluating" || (a.pending_follow_up && a.pending_follow_up.question_pending);
    if (!pending) return a;
    await sleep(400);
  }
  throw new Error("feedback never arrived");
}

const inTen = new Date(Date.now() + 10 * 86400000).toISOString().slice(0, 10);
await call("POST", "/v1/me/goal", { job_type: "verification", interview_date: inTen, minutes_per_day: 20, seniority: "student", language: "he" });
await call("GET", "/v1/me/program?language=he");
// attempt A: weak answer -> feedback + follow-up answered -> next question suggested (the complete practice flow)
const a = await call("POST", "/v1/practice/attempts", { question_key: "example-sensor-majority", mode: "deep", language: "he" });
await call("POST", `/v1/practice/attempts/${a.id}/submissions`, { answer: { text: "alarm = A ^ B ^ C" } });
let aView = await waitWords(a.id);
if (aView.pending_follow_up) {
  await call("POST", `/v1/practice/attempts/${a.id}/follow-ups/${aView.pending_follow_up.turn}/submissions`, { answer: { text: "majority = AB + BC + AC; the stuck sensor forces two rows to 1" } });
  aView = await waitWords(a.id);
}
// attempt B (English): answered, follow-up still waiting for an answer
const b = await call("POST", "/v1/practice/attempts", { question_key: "example-sensor-majority", mode: "deep", language: "en" });
await call("POST", `/v1/practice/attempts/${b.id}/submissions`, { answer: { text: "alarm = A ^ B ^ C" } });
await waitWords(b.id);
// one program item started and left open, so Learn photographs the day's sheet with a current item ("Continue")
const program = await call("GET", "/v1/me/program?language=he");
if (program.next && program.next.mode !== "simulation") {
  await call("POST", "/v1/me/program/start", { item_id: program.next.id, language: "he" });
}
// interviews: one in progress (room), one finished (report)
// two more scored answers on earlier days, so "The road so far" has three days to draw
// the expression must be right, or the automatic truth-table check caps the band at "needs work"
for (const [days, text] of [[2, "A strong, complete derivation: alarm = AB + BC + AC, read from the truth-table rows with two or more ones."], [1, "A partial answer that names the constraint: alarm = AB + BC + AC."]]) {
  const past = await call("POST", "/v1/practice/attempts", { question_key: "example-sensor-majority", mode: "quick", language: "he" });
  await call("POST", `/v1/practice/attempts/${past.id}/submissions`, { answer: { text } });
  await waitWords(past.id);
  await call("POST", "/__harness/backdate", { attempt_id: past.id, days });
}
const room = await call("POST", "/v1/interviews", { duration_min: 20, language: "he" });
await call("POST", `/v1/interviews/${room.id}/turns/0/answer`, { answer: "A careful answer that states the assumptions and derives the result." });
const done = await call("POST", "/v1/interviews", { duration_min: 20, language: "he" });
await call("POST", `/v1/interviews/${done.id}/turns/0/answer`, { answer: "A careful answer that states the assumptions and derives the result." });
await call("POST", `/v1/interviews/${done.id}/turns/1/answer`, { answer: "A partial answer that gets the idea but not the timing arithmetic." });
await call("POST", `/v1/interviews/${done.id}/turns/2/answer`, { answer: "A strong answer with the state table and the reset path." });
await call("POST", `/v1/interviews/${done.id}/end`);
await call("GET", `/v1/interviews/${done.id}/report`);
log("seeded: attempts", a.id.slice(0, 8), b.id.slice(0, 8), "interviews", room.id.slice(0, 8), done.id.slice(0, 8));

// ------------------------------------------------------------------------------------------ the web app

// A production build (NEXT_PUBLIC_* values are baked in at build time), so the pages look as deployed and carry no
// dev overlay; --dev uses the dev server instead (faster to start, slower per page).
const webEnv = { ...process.env, NEXT_PUBLIC_API_BASE_URL: api, NEXT_PUBLIC_SUPABASE_URL: `http://localhost:${STUB_PORT}`, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: "screenshot-key", NEXT_TELEMETRY_DISABLED: "1" };
const npx = process.platform === "win32" ? "npx.cmd" : "npx";
if (args.dev) {
  start(npx, ["next", "dev", "-p", String(WEB_PORT)], { cwd: webDir, name: "next", shell: true, env: webEnv });
} else {
  log("building the web app (about a minute)");
  await new Promise((resolveBuild, rejectBuild) => {
    const b = spawn(npx, ["next", "build"], { cwd: webDir, shell: true, env: webEnv, stdio: ["ignore", "pipe", "pipe"] });
    let out = "";
    b.stdout.on("data", (d) => { out += d; });
    b.stderr.on("data", (d) => { out += d; });
    b.on("exit", (code) => (code === 0 ? resolveBuild() : rejectBuild(new Error(`next build failed:
${out.slice(-2000)}`))));
  });
  start(npx, ["next", "start", "-p", String(WEB_PORT)], { cwd: webDir, name: "next", shell: true, env: webEnv });
}
await waitFor(`http://localhost:${WEB_PORT}/`, 240, (r) => r.status < 500);
await fetch(`http://localhost:${WEB_PORT}/`).then((r) => r.text());
log("web up");

// ------------------------------------------------------------------------------------------ the browser

const profile = join(OUT, `edge-profile-${process.pid}`);          // a fresh profile: a locked one from a killed run never blocks
rmSync(profile, { recursive: true, force: true });
const port = 9300 + Math.floor(Math.random() * 500);
start(EDGE, ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "about:blank"], { name: "edge" });
let target;
for (let i = 0; i < 300 && !target; i++) {                             // a cold start of Edge can take a while
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === "page"); } catch {}
}
if (!target) throw new Error("no DevTools target after 60 s");
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let id = 0; const pending = new Map(); const consoleErrors = [];
ws.addEventListener("message", (e) => {
  const msg = JSON.parse(e.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  if (msg.method === "Runtime.exceptionThrown") consoleErrors.push(msg.params.exceptionDetails?.exception?.description ?? "exception");
  if (msg.method === "Runtime.consoleAPICalled" && msg.params.type === "error") consoleErrors.push(msg.params.args.map((x) => x.value ?? x.description).join(" "));
});
const send = (method, params = {}) => new Promise((r) => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
await send("Page.enable"); await send("Runtime.enable");

const storageKey = `sb-${new URL(`http://localhost:${STUB_PORT}`).hostname.split(".")[0]}-auth-token`;
const inject = (lang, signedIn) => `
  try {
    window.__lcp = 0; window.__cls = 0;
    new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__lcp = e.startTime; }).observe({ type: "largest-contentful-paint", buffered: true });
    new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; }).observe({ type: "layout-shift", buffered: true });
  } catch (e) {}
  try {
    localStorage.setItem("jobrun-language", ${JSON.stringify(lang)});
    ${signedIn ? `localStorage.setItem(${JSON.stringify(storageKey)}, ${JSON.stringify(JSON.stringify(session))});` : `localStorage.removeItem(${JSON.stringify(storageKey)});`}
    localStorage.setItem("jobrun-goal-skipped-${session.user.id}", "1");
  } catch (e) {}`;

const SCREENS = [
  ["signin", "/", false, ".landing"],
  ["learn", "/", true, ".learn, .path-card"],
  ["library", "/?view=library", true, ".question-table, .question-row"],
  ["question", "/?question=example-sensor-majority", true, ".question-sheet"],
  ["practice-done", `/?attempt=${a.id}`, true, ".evaluation, .practice-flow"],
  ["practice-followup", `/?attempt=${b.id}`, true, ".follow-ups, .practice-flow"],
  ["progress", "/?view=progress", true, ".progress-board, .plan-table"],
  ["interview-lobby", "/?view=interview", true, ".interview-lobby, .interview-setup"],
  ["interview-room", `/?view=interview&interview=${room.id}`, true, ".interview-room"],
  ["interview-report", `/?view=interview&interview=${done.id}`, true, ".interview-report"],
  // the same screens with a Radix layer open: a select, the hint popover, the language menu
  ["library-topic-open", "/?view=library", true, ".ui-select-trigger", ".ui-select-trigger"],
  ["hint-help-open", `/?attempt=${a.id}`, true, ".help-trigger", ".help-trigger"],
  ["language-menu-open", "/", true, ".language-switch", ".language-switch"],
  ["report-open", "/?question=example-sensor-majority", true, ".report-trigger", ".report-trigger"],
];
const index = [];
for (const lang of LANGS) {
  for (const width of WIDTHS) {
    const height = width < 600 ? 844 : 900;
    await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
    for (const [name, path, signedIn, selector, open] of SCREENS) {
      consoleErrors.length = 0;
      const { identifier } = (await send("Page.addScriptToEvaluateOnNewDocument", { source: inject(lang, signedIn) })).result;
      await send("Page.navigate", { url: `http://localhost:${WEB_PORT}${path}` });
      let found = false;
      for (let i = 0; i < 60 && !found; i++) {
        await sleep(500);
        const r = await send("Runtime.evaluate", { expression: `!!document.querySelector(${JSON.stringify(selector)})`, returnByValue: true });
        found = r.result?.result?.value === true;
      }
      if (found && open) {
        // a real pointer press on the element's centre, so Radix's pointerdown handlers open it
        const r = await send("Runtime.evaluate", { expression: `(() => { const b = document.querySelector(${JSON.stringify(open)}).getBoundingClientRect(); return JSON.stringify({x: b.left + b.width / 2, y: b.top + b.height / 2}); })()`, returnByValue: true });
        const { x, y } = JSON.parse(r.result?.result?.value ?? "{}");
        for (const type of ["mouseMoved", "mousePressed", "mouseReleased"]) {
          await send("Input.dispatchMouseEvent", { type, x, y, button: "left", clickCount: 1, pointerType: "mouse" });
        }
        await sleep(700);
      }
      // long enough for the grade sequence (1.3 s) and the path's staggered arrival to finish
      await sleep(found ? 2000 : 0);
      // layout facts plus the page's own timing: first paint, largest paint, layout shift, load, script bytes
      const metrics = await send("Runtime.evaluate", { expression: `JSON.stringify((() => {
        const nav = performance.getEntriesByType("navigation")[0] || {};
        const fcp = performance.getEntriesByName("first-contentful-paint")[0];
        const res = performance.getEntriesByType("resource");
        const kb = (t) => Math.round(res.filter((r) => r.initiatorType === t).reduce((a, r) => a + (r.transferSize || 0), 0) / 1024);
        return { inner: innerWidth, scroll: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight, title: document.title, dir: document.documentElement.dir,
          fcp_ms: fcp ? Math.round(fcp.startTime) : null, lcp_ms: Math.round(window.__lcp || 0) || null, cls: Math.round((window.__cls || 0) * 1000) / 1000,
          dcl_ms: Math.round(nav.domContentLoadedEventEnd || 0) || null, load_ms: Math.round(nav.loadEventEnd || 0) || null,
          js_kb: kb("script"), css_kb: kb("link"), font_kb: kb("css") + kb("other"), heap_mb: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : null };
      })())`, returnByValue: true });
      const info = JSON.parse(metrics.result?.result?.value ?? "{}");
      const file = `${name}-${lang}-${width}.png`;
      const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
      writeFileSync(join(OUT, file), Buffer.from(shot.result.data, "base64"));
      // a full-page capture too, for scrolling screens
      const full = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width, height: Math.min(info.height || height, 4000), scale: 1 } });
      writeFileSync(join(OUT, `${name}-${lang}-${width}-full.png`), Buffer.from(full.result.data, "base64"));
      index.push({ file, name, lang, width, found, ...info, overflow: (info.scroll ?? 0) > (info.inner ?? 0), console_errors: [...consoleErrors] });
      await send("Page.removeScriptToEvaluateOnNewDocument", { identifier });
      log(file, found ? "" : "(selector not found)", info.scroll > info.inner ? `OVERFLOW ${info.scroll}>${info.inner}` : "");
    }
  }
}
writeFileSync(join(OUT, "index.json"), JSON.stringify(index, null, 2));
const med = (xs) => { const a = xs.filter((x) => typeof x === "number").sort((p, q) => p - q); return a.length ? a[Math.floor(a.length / 2)] : null; };
const worst = (xs) => Math.max(...xs.filter((x) => typeof x === "number"), 0);
for (const width of WIDTHS) {
  const rows = index.filter((r) => r.width === width);
  log(`timing @${width}: FCP median ${med(rows.map((r) => r.fcp_ms))} ms (worst ${worst(rows.map((r) => r.fcp_ms))}), LCP median ${med(rows.map((r) => r.lcp_ms))} ms (worst ${worst(rows.map((r) => r.lcp_ms))}), CLS worst ${worst(rows.map((r) => r.cls))}, load median ${med(rows.map((r) => r.load_ms))} ms, JS ${med(rows.map((r) => r.js_kb))} KB, heap ${med(rows.map((r) => r.heap_mb))} MB`);
}
ws.close();
const overflow = index.filter((s) => s.overflow).map((s) => s.file);
const missing = index.filter((s) => !s.found).map((s) => s.file);
log(`done: ${index.length} shots in ${OUT}; overflow: ${overflow.length ? overflow.join(", ") : "none"}; not found: ${missing.length ? missing.join(", ") : "none"}`);
stopAll();
try { rmSync(profile, { recursive: true, force: true }); } catch {}   // Edge may still hold the profile for a moment
process.exit(0);
