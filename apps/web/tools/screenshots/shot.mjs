// One screenshot of any URL through headless Edge and the DevTools protocol, with device emulation, so it works
// even while a normal Edge window is open (plain --screenshot hands off to the running browser and produces nothing).
//   node tools/screenshots/shot.mjs <url> <out.png> [width] [height]
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [url, out, w = "1280", h = "1000"] = process.argv.slice(2);
if (!url || !out) {
  console.error("usage: node shot.mjs <url> <out.png> [width] [height]");
  process.exit(2);
}
const width = Number(w), height = Number(h);
const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Google/Chrome/Application/chrome.exe"].find(existsSync);
const profile = join(tmpdir(), `shot-profile-${process.pid}`);
mkdirSync(profile, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// a free port, then poll /json the way run.mjs does (Edge's stderr is not reliable for the endpoint)
const { createServer } = await import("node:net");
const port = await new Promise((r) => { const srv = createServer(); srv.listen(0, () => { const p = srv.address().port; srv.close(() => r(p)); }); });
const edge = spawn(EDGE, ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
let page;
for (let i = 0; i < 300 && !page; i++) {
  await sleep(200);
  try { page = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === "page"); } catch {}
}
if (!page) { edge.kill(); throw new Error("no DevTools target after 60 s"); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const waiting = new Map();
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); } };
const send = (method, params = {}) => new Promise((r) => { const n = ++id; waiting.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
await send("Page.navigate", { url });
await sleep(2500);
const metrics = await send("Runtime.evaluate", { expression: "JSON.stringify({scroll: document.documentElement.scrollWidth, inner: innerWidth, height: document.documentElement.scrollHeight})", returnByValue: true });
const info = JSON.parse(metrics.result?.result?.value ?? "{}");
const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width, height: Math.min(info.height || height, 5000), scale: 1 } });
writeFileSync(out, Buffer.from(shot.result.data, "base64"));
console.log(`${out} ${width}x${Math.min(info.height || height, 5000)}${info.scroll > info.inner ? ` OVERFLOW ${info.scroll}>${info.inner}` : ""}`);
ws.close(); edge.kill();
await sleep(300);
try { rmSync(profile, { recursive: true, force: true }); } catch {}
