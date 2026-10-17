// Focused, local-only UI regression for the circuit workspace. Reuses an existing
// preview server and launches its own headless Edge with a fresh temporary profile.
//   node tools/screenshots/circuit-workspace.mjs --url http://localhost:3212/site-preview?style=ion-adaptive --out .impeccable/review/circuit-workspace
// No application account, backend, browser profile, or existing server is touched.
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { basename, dirname, isAbsolute, join, resolve } from "node:path";

const args = {};
for (let i = 2; i < process.argv.length; i++) {
  const key = process.argv[i];
  if (!key.startsWith("--") || !process.argv[i + 1]) throw new Error(`Expected --name value, received ${key}`);
  args[key.slice(2)] = process.argv[++i];
}
const url = new URL(args.url ?? "http://localhost:3212/site-preview?style=ion-adaptive");
if (!["localhost", "127.0.0.1", "[::1]"].includes(url.hostname) || url.pathname !== "/site-preview") {
  throw new Error("This runner only supports a local /site-preview URL.");
}
url.searchParams.set("screen", "practice");
url.searchParams.set("question", "xor");
url.searchParams.set("motion", "0");
const out = resolve(args.out ?? join(".impeccable", "review", "circuit-workspace"));
const edge = process.env.EDGE_PATH ?? "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const delay = (ms) => new Promise((r) => setTimeout(r, ms));
const started = Date.now();
const checks = [], screenshots = [], scenarios = [], errors = [];
let browser, ws, profile, cleaned = false;

function cleanup() {
  if (cleaned) return;
  cleaned = true;
  try { ws?.close(); } catch {}
  if (browser?.pid) {
    try {
      if (process.platform === "win32") spawnSync("taskkill", ["/pid", String(browser.pid), "/T", "/F"], { stdio: "ignore", windowsHide: true });
      else browser.kill();
    } catch {}
  }
  // Only remove the absolute, generated profile directly under the OS temp dir.
  // Never recursively delete an output directory or a caller-supplied path.
  if (profile && isAbsolute(profile) && dirname(profile) === resolve(tmpdir()) && basename(profile).startsWith("jobrun-circuit-workspace-")) {
    try { rmSync(profile, { recursive: true, force: true, maxRetries: 8, retryDelay: 150 }); } catch {}
  }
}
process.on("exit", cleanup);
process.on("SIGINT", () => { cleanup(); process.exit(130); });
process.on("SIGTERM", () => { cleanup(); process.exit(143); });

function check(name, pass, detail = undefined) {
  checks.push({ scenario: current, name, pass: !!pass, ...(detail === undefined ? {} : { detail }) });
  if (!pass) console.error(`FAIL ${current}: ${name}${detail === undefined ? "" : ` ${JSON.stringify(detail)}`}`);
}
let current = "startup";
let sequence = 0;
const pending = new Map();
function send(method, params = {}) {
  return new Promise((resolveCall, reject) => {
    const id = ++sequence;
    const timeout = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 20000);
    pending.set(id, (message) => {
      clearTimeout(timeout);
      if (message.error) reject(new Error(`${method}: ${JSON.stringify(message.error)}`));
      else resolveCall(message.result);
    });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text);
  return result.result.value;
}
async function waitFor(expression, description, timeout = 30000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    try { if (await evaluate(expression)) return; } catch {}
    await delay(100);
  }
  throw new Error(`Timed out waiting for ${description}`);
}
async function click(expression) {
  const point = await evaluate(`(() => {
    const e = ${expression};
    if (!e) throw new Error('Click target absent: ' + ${JSON.stringify(expression)});
    if (e.disabled) throw new Error('Click target disabled: ' + e.outerHTML);
    e.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'});
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) throw new Error('Click target has no area');
    const x = r.left+r.width/2, y = r.top+r.height/2;
    const hit = document.elementFromPoint(x,y);
    if (hit !== e && !e.contains(hit)) throw new Error('Click target obscured: ' + e.outerHTML);
    return {x,y};
  })()`);
  for (const type of ["mouseMoved", "mousePressed", "mouseReleased"]) {
    await send("Input.dispatchMouseEvent", { type, ...point, button: "left", clickCount: 1, pointerType: "mouse" });
  }
  await delay(120);
}
const button = (text, scope = "document") => `Array.from(${scope}.querySelectorAll('button')).find(e => e.textContent.trim() === ${JSON.stringify(text)})`;
const named = (label) => `document.querySelector('button[aria-label=' + ${JSON.stringify(JSON.stringify(label))} + ']')`;
async function screenshot(name) {
  const file = `${name}.png`;
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  writeFileSync(join(out, file), Buffer.from(shot.data, "base64"));
  screenshots.push({ scenario: current, file });
}
async function settleViewport() {
  let previous, stable = 0;
  for (let i = 0; i < 30; i++) {
    const transform = await evaluate("(() => { const e=document.querySelector('dialog .react-flow__viewport'); return e ? getComputedStyle(e).transform : null; })()");
    stable = transform && transform === previous ? stable + 1 : 0;
    if (stable >= 3) return transform;
    previous = transform;
    await delay(100);
  }
  throw new Error("ReactFlow viewport transform did not settle");
}
async function facts() {
  await settleViewport();
  return evaluate(`(() => {
    const d = document.querySelector('dialog[data-layout]'), r=d.getBoundingClientRect();
    const flow=d.querySelector('.react-flow'), aside=d.querySelector('aside');
    const controls=Array.from(d.querySelectorAll('.circuit-toolbar button'));
    const back=controls.at(-1), b=back.getBoundingClientRect(), hit=document.elementFromPoint(b.x+b.width/2,b.y+b.height/2);
    const selected=d.querySelector('.component-picker select');
    const visibleHeight=(element)=>{
      if(!element) return 0;
      const rect=element.getBoundingClientRect();
      let top=Math.max(0,rect.top),bottom=Math.min(innerHeight,rect.bottom);
      for(let parent=element.parentElement;parent;parent=parent.parentElement){
        if(/auto|scroll|hidden|clip/.test(getComputedStyle(parent).overflowY)){
          const clip=parent.getBoundingClientRect();
          top=Math.max(top,clip.top+parent.clientTop);
          bottom=Math.min(bottom,clip.top+parent.clientTop+parent.clientHeight);
        }
      }
      return Math.max(0,bottom-top);
    };
    const flowViewport=flow.querySelector('.react-flow__viewport');
    return {
      layout:d.dataset.layout, modal:d.matches(':modal'), open:d.open,
      rect:{x:r.x,y:r.y,width:r.width,height:r.height}, viewport:{width:innerWidth,height:innerHeight},
      bodyOverflow:document.body.style.overflow, pageWidth:document.documentElement.scrollWidth,
      dialogWidth:d.scrollWidth, dialogClientWidth:d.clientWidth,
      sameFlow:flow === window.__circuitFlow, sameDialog:d === window.__circuitDialog,
      viewportTransform:getComputedStyle(flowViewport).transform,
      viewportStyleTransform:flowViewport.style.transform,
      canvasVisiblePixels:visibleHeight(d.querySelector('.circuit-canvas')),
      nodes:d.querySelectorAll('.react-flow__node').length, selected:selected?.value ?? null,
      selectedNode:!!d.querySelector('.react-flow__node.selected'),
      simulationRunning:!!d.querySelector('.simulation-bar button[aria-pressed="true"]'),
      clock:d.querySelector('.simulation-bar button:nth-child(2)')?.textContent.trim() ?? null,
      question:aside ? {text:aside.textContent.trim(),height:aside.getBoundingClientRect().height,scrollHeight:aside.scrollHeight,clientHeight:aside.clientHeight,textVisiblePixels:visibleHeight(aside.querySelector('p'))} : null,
      closeAccessible:b.width>=43 && b.height>=43 && b.x>=-1 && b.y>=-1 && b.right<=innerWidth+1 && b.bottom<=innerHeight+1 && (hit===back||back.contains(hit)),
      activeIsBack:document.activeElement===back
    };
  })()`);
}
function assertCommon(state, label) {
  check(`${label}: ReactFlow DOM retained`, state.sameFlow);
  check(`${label}: dialog DOM retained`, state.sameDialog);
  check(`${label}: viewport transform retained`, state.viewportTransform === baselineTransform, { before: baselineTransform, after: state.viewportTransform });
  check(`${label}: no horizontal page overflow`, state.pageWidth <= state.viewport.width + 1, { page: state.pageWidth, viewport: state.viewport.width });
  check(`${label}: no horizontal dialog overflow`, state.dialogWidth <= state.dialogClientWidth + 1, { scroll: state.dialogWidth, client: state.dialogClientWidth });
  check(`${label}: gate retained`, state.nodes === 1, state.nodes);
  check(`${label}: selection retained`, state.selected === selectedId && state.selectedNode, { selected: state.selected, selectedNode: state.selectedNode });
  check(`${label}: simulation retained`, state.simulationRunning && /1$/.test(state.clock ?? ""), state.clock);
}
let selectedId, baselineTransform;

try {
  // Fail promptly if the caller's preview server is unavailable; do not start one.
  const response = await fetch(url, { signal: AbortSignal.timeout(12000) });
  if (!response.ok) throw new Error(`Existing preview server returned ${response.status}: ${url}`);
  mkdirSync(out, { recursive: true });
  const port = await new Promise((resolvePort) => {
    const server = createServer();
    server.listen(0, "127.0.0.1", () => { const { port } = server.address(); server.close(() => resolvePort(port)); });
  });
  profile = resolve(mkdtempSync(join(tmpdir(), "jobrun-circuit-workspace-")));
  browser = spawn(edge, ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore", windowsHide: true });
  browser.on("error", (error) => errors.push(error.message));
  let target;
  for (let i = 0; i < 120 && !target; i++) {
    await delay(200);
    try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === "page"); } catch {}
  }
  if (!target) throw new Error(`No isolated Edge DevTools target. ${errors.join(" ")}`);
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r, reject) => { ws.addEventListener("open", r, { once: true }); ws.addEventListener("error", reject, { once: true }); });
  ws.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) { pending.get(message.id)(message); pending.delete(message.id); }
    if (message.method === "Runtime.exceptionThrown") errors.push({ scenario: current, error: message.params.exceptionDetails.exception?.description ?? message.params.exceptionDetails.text });
    if (message.method === "Runtime.consoleAPICalled" && message.params.type === "error") errors.push({ scenario: current, error: message.params.args.map((a) => a.value ?? a.description).join(" ") });
  });
  await send("Page.enable");
  await send("Runtime.enable");
  for (const config of [
    { name: "desktop", width: 1440, height: 1000, lang: "he", dark: false },
    { name: "desktop", width: 1440, height: 1000, lang: "en", dark: true },
    { name: "mobile", width: 390, height: 844, lang: "he", dark: false },
    { name: "mobile", width: 390, height: 844, lang: "en", dark: true },
  ]) {
    current = `${config.name}-${config.lang}-${config.dark ? "dark" : "light"}`;
    const scenario = { ...config, name: current, states: {} };
    scenarios.push(scenario);
    try {
      await send("Emulation.setDeviceMetricsOverride", { width: config.width, height: config.height, deviceScaleFactor: 1, mobile: config.name === "mobile" });
      const documentToken = `${current}-${Date.now()}`;
      const { identifier } = await send("Page.addScriptToEvaluateOnNewDocument", { source: `window.__qaDocument=${JSON.stringify(documentToken)}` });
      await send("Page.navigate", { url: url.toString() });
      await waitFor(`window.__qaDocument===${JSON.stringify(documentToken)} && document.readyState==='complete' && (()=>{const e=document.querySelector('#answer-tab-circuit');return !!e && Object.keys(e).some(k=>k.startsWith('__reactProps') && typeof e[k]?.onClick==='function')})()`, "hydrated practice answer tabs");
      await send("Page.removeScriptToEvaluateOnNewDocument", { identifier });
      console.log(`OPEN ${current}`);
      if (config.lang === "en") await click(named("Switch to English"));
      if (config.dark) await click(named(config.lang === "en" ? "Switch to dark mode" : "מעבר למצב כהה"));
      await click("document.querySelector('#answer-tab-circuit')");
      await waitFor("!!document.querySelector('dialog[data-layout=inline] .react-flow')", "inline circuit editor");
      const t = (he, en) => config.lang === "he" ? he : en;
      await evaluate("window.__circuitFlow=document.querySelector('dialog .react-flow');window.__circuitDialog=document.querySelector('dialog[data-layout]');window.__bodyOverflow=document.body.style.overflow");
      check("inline is nonmodal", await evaluate("!window.__circuitDialog.matches(':modal')"));
      await click(button("AND", "document.querySelector('.component-palette')"));
      await waitFor("document.querySelectorAll('.react-flow__node').length===1", "new gate");
      await delay(200);
      selectedId = await evaluate("document.querySelector('.component-picker select').value");
      check("add selects gate", !!selectedId);
      await click(named(t("ביטול שינוי במעגל", "Undo circuit change")));
      check("undo removes gate", await evaluate("document.querySelectorAll('.react-flow__node').length===0"));
      await click(named(t("ביצוע שינוי מחדש במעגל", "Redo circuit change")));
      check("redo restores gate and selection", await evaluate(`document.querySelectorAll('.react-flow__node').length===1 && document.querySelector('.component-picker select').value===${JSON.stringify(selectedId)}`));
      await click(button(t("הרצת סימולציה", "Run simulation")));
      await click(`document.querySelector('.simulation-bar button:nth-child(2)')`);
      const inlineState = await facts();
      baselineTransform = inlineState.viewportTransform;
      scenario.states.inline = inlineState;
      check("inline viewport transform recorded", !!baselineTransform && baselineTransform !== "none", baselineTransform);
      await click(button(t("הרחבת הלוח", "Expand drawing")));
      await waitFor("document.querySelector('dialog').matches(':modal')", "expanded native modal");
      await evaluate("document.querySelector('.component-library').parentElement.scrollTop=0");
      let state = await facts();
      scenario.states.expanded = state;
      assertCommon(state, "expanded");
      check("expanded has native modality", state.modal && state.layout === "expanded" && state.bodyOverflow === "hidden");
      check("question text is visible", state.question?.text.length > 50 && state.question.height > 100, state.question);
      check("expanded close button accessible", state.closeAccessible);
      await screenshot(`${config.name === "mobile" ? "mobile-question" : "desktop-expanded"}-${config.lang}-${config.dark ? "dark" : "light"}`);
      if (config.name === "mobile") {
        await evaluate("document.querySelector('.circuit-canvas').scrollIntoView({block:'center',behavior:'instant'})");
        const questionCanvas = await facts();
        scenario.states.questionCanvas = questionCanvas;
        check("mobile question and canvas visible together", questionCanvas.canvasVisiblePixels >= 200 && questionCanvas.question?.textVisiblePixels >= 20, { canvasPixels: questionCanvas.canvasVisiblePixels, questionTextPixels: questionCanvas.question?.textVisiblePixels });
        await screenshot(`mobile-question-canvas-${config.lang}-${config.dark ? "dark" : "light"}`);
      }
      await click(named(t("סגירת תצוגת השאלה", "Close question reference")));
      check("question close hides reference", await evaluate("!document.querySelector('dialog aside')"));
      await click(button(t("הצגת השאלה", "Show question")));
      check("question can reopen", await evaluate("!!document.querySelector('dialog aside')"));
      await click(button(t("מסך מלא", "Full screen")));
      state = await facts();
      scenario.states.fullscreen = state;
      assertCommon(state, "fullscreen");
      check("fullscreen fills viewport", state.modal && state.layout === "fullscreen" && Math.abs(state.rect.x) < 1 && Math.abs(state.rect.y) < 1 && Math.abs(state.rect.width-config.width) < 1 && Math.abs(state.rect.height-config.height) < 1, state.rect);
      check("fullscreen close button accessible", state.closeAccessible);
      if (config.name === "mobile") {
        await click(button(t("הסתרת השאלה", "Hide question")));
        await evaluate("document.querySelector('.circuit-canvas').scrollIntoView({block:'center',behavior:'instant'})");
      }
      await screenshot(`${config.name === "mobile" ? "mobile-canvas" : "desktop-fullscreen"}-${config.lang}-${config.dark ? "dark" : "light"}`);
      await click(button(t("חלון מוגדל", "Expanded window")));
      state = await facts();
      scenario.states.reexpanded = state;
      assertCommon(state, "return to expanded");
      check("fullscreen can return to expanded", state.modal && state.layout === "expanded");
      await click(button(t("חזרה לתשובה", "Back to answer")));
      state = await facts();
      scenario.states.closed = state;
      assertCommon(state, "back to answer");
      check("back restores inline, scroll and focus", !state.modal && state.layout === "inline" && state.bodyOverflow === await evaluate("window.__bodyOverflow") && state.activeIsBack, state);
      await click(button(t("הרחבת הלוח", "Expand drawing")));
      await waitFor("document.querySelector('dialog').matches(':modal')", "modal for Escape");
      await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
      await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
      await delay(120);
      state = await facts();
      scenario.states.escape = state;
      assertCommon(state, "Escape");
      check("Escape restores inline, scroll and focus", !state.modal && state.layout === "inline" && state.bodyOverflow === await evaluate("window.__bodyOverflow") && state.activeIsBack);
      // History survives the complete modal cycle, including the simulation state.
      await click(named(t("ביטול שינוי במעגל", "Undo circuit change")));
      check("undo history survives modes", await evaluate("document.querySelectorAll('.react-flow__node').length===0"));
      await click(named(t("ביצוע שינוי מחדש במעגל", "Redo circuit change")));
      check("redo history survives modes", await evaluate("document.querySelectorAll('.react-flow__node').length===1"));
      const scenarioChecks = checks.filter((c) => c.scenario === current);
      console.log(`${scenarioChecks.every((c) => c.pass) ? "PASS" : "FAIL"} ${current}: ${scenarioChecks.filter((c) => c.pass).length}/${scenarioChecks.length} checks`);
    } catch (error) {
      check("scenario completed", false, error.message);
      scenario.error = error.message;
      try { await screenshot(`failure-${current}`); } catch {}
    }
  }
} catch (error) {
  check("runner startup", false, error.message);
} finally {
  current = "browser";
  check("no browser console errors or uncaught exceptions", errors.length === 0, errors);
  const failed = checks.filter((c) => !c.pass);
  const report = { url: url.toString(), elapsedSeconds: Math.round((Date.now()-started)/1000), total: checks.length, passed: checks.length-failed.length, failed: failed.length, checks, screenshots, scenarios, consoleErrors: errors };
  mkdirSync(out, { recursive: true });
  writeFileSync(join(out, "results.json"), JSON.stringify(report, null, 2));
  console.log(`${report.passed}/${report.total} checks passed; ${screenshots.length} screenshots; ${errors.length} console errors. Results: ${join(out, "results.json")}`);
  cleanup();
  process.exitCode = failed.length ? 1 : 0;
}
