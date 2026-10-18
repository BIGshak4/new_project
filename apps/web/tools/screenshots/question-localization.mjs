// Local regression of the real study renderer, bundled into a temporary fixture.
// node tools/screenshots/question-localization.mjs
// Uses seed files and an isolated headless Edge profile. No application accounts or API requests.
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { basename, dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";

const web = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const outFlag = process.argv.indexOf("--out");
const out = resolve(outFlag >= 0 ? process.argv[outFlag + 1] : join(web, "../../.impeccable/review/question-localization"));
const edge = process.env.EDGE_PATH ?? "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const questions = JSON.parse(readFileSync(join(web, "../../backend/seeds/questions/preparation_bank.json"), "utf8"));
if (questions.length !== 43 || questions.some(q => !q.assets.preparation_resource.learner_material)) {
  throw new Error("Regenerate the 43 preparation resources with their paired learner_material before running.");
}
const checks = [], screenshots = [], errors = [];
const started = Date.now();
let fixture, browser, ws, server, cleaned = false, sequence = 0;
const pending = new Map();
const delay = ms => new Promise(done => setTimeout(done, ms));
function check(name, pass, detail) {
  checks.push({ name, pass: !!pass, ...(detail === undefined ? {} : { detail }) });
  if (!pass) console.error(`FAIL ${name}: ${JSON.stringify(detail)}`);
}
function cleanup() {
  if (cleaned) return;
  cleaned = true;
  try { ws?.close(); } catch {}
  try { server?.close(); } catch {}
  if (browser?.pid) {
    try {
      if (process.platform === "win32") spawnSync("taskkill", ["/pid", String(browser.pid), "/T", "/F"], { stdio: "ignore", windowsHide: true });
      else browser.kill();
    } catch {}
  }
  // Delete only the generated, resolved fixture/profile directly below the OS temp directory.
  if (fixture && isAbsolute(fixture) && dirname(fixture) === resolve(tmpdir()) && basename(fixture).startsWith("jobrun-question-localization-")) {
    try { rmSync(fixture, { recursive: true, force: true, maxRetries: 8, retryDelay: 150 }); } catch {}
  }
}
process.on("exit", cleanup);
process.on("SIGINT", () => { cleanup(); process.exit(130); });
process.on("SIGTERM", () => { cleanup(); process.exit(143); });
function send(method, params = {}) {
  return new Promise((done, reject) => {
    const id = ++sequence;
    const timeout = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 20000);
    pending.set(id, message => {
      clearTimeout(timeout);
      if (message.error) reject(new Error(`${method}: ${JSON.stringify(message.error)}`));
      else done(message.result);
    });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text);
  return result.result.value;
}
async function waitFor(expression, description, timeout = 15000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await evaluate(expression)) return;
    await delay(40);
  }
  throw new Error(`Timed out waiting for ${description}`);
}
async function click(selector) {
  const point = await evaluate(`(() => {
    const element = document.querySelector(${JSON.stringify(selector)});
    if (!element) throw new Error('Missing target ' + ${JSON.stringify(selector)});
    element.scrollIntoView({block:'center',behavior:'instant'});
    const r=element.getBoundingClientRect();
    const x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);
    if (!r.width || !r.height || (hit!==element && !element.contains(hit))) throw new Error('Obscured target');
    return {x,y};
  })()`);
  for (const type of ["mousePressed", "mouseReleased"]) {
    await send("Input.dispatchMouseEvent", { type, ...point, button: "left", clickCount: 1 });
  }
  await delay(25);
}
async function screenshot(name) {
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  writeFileSync(join(out, `${name}.png`), Buffer.from(shot.data, "base64"));
  screenshots.push(`${name}.png`);
}
async function openSections() {
  const count = await evaluate("document.querySelectorAll('.technical-material > details').length");
  for (let i = 0; i < count; i++) await click(`.technical-material > details:nth-of-type(${i + 1}) > summary`);
  return count;
}
async function facts() {
  return evaluate(`(() => ({
    key:document.querySelector('main').dataset.key,
    lang:document.querySelector('main').dataset.lang,
    status:document.querySelector('main').dataset.status,
    reference:document.querySelector('#reference')?.textContent ?? '',
    main:document.querySelector('main').textContent,
    open:document.querySelectorAll('.technical-material > details[open]').length,
    summaries:Array.from(document.querySelectorAll('.technical-material > details > summary'),e=>e.textContent),
    overflow:document.documentElement.scrollWidth>innerWidth+1,
  }))()`);
}

try {
  mkdirSync(out, { recursive: true });
  fixture = resolve(mkdtempSync(join(tmpdir(), "jobrun-question-localization-")));
  const source = `import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import {StudyText, TechnicalMaterial} from './src/components/question-materials';
import {referenceInLanguage} from './src/lib/material-locale';
const questions=${JSON.stringify(questions)};
function Fixture(){
 const [index,setIndex]=useState(Number(new URLSearchParams(location.search).get('index')||0));
 const [lang,setLang]=useState('he');
 const [status,setStatus]=useState('loaded');
 const question=questions[index],material=question.assets.preparation_resource;
 const resources=status==='pending'?null:status==='legacy'?{media:[],solution_revealed:true,technical_material:material}:
 {media:[],solution_revealed:true,technical_material:material,language:lang,reference:question.translations[lang].reference_solution};
 const reference=referenceInLanguage(resources,lang,question.translations.he.reference_solution,'he');
 return <><nav aria-label='Local regression fixture'>
 <button id='he' onClick={()=>setLang('he')}>Hebrew</button><button id='en' onClick={()=>setLang('en')}>English</button>
 <button id='pending' onClick={()=>setStatus('pending')}>Pending resources</button><button id='loaded' onClick={()=>setStatus('loaded')}>Loaded resources</button>
 <button id='legacy' onClick={()=>setStatus('legacy')}>Legacy resources</button><button id='next' onClick={()=>{setIndex((index+1)%questions.length);setStatus('loaded');}}>Next question</button>
 </nav><main key={question.key} data-key={question.key} data-lang={lang} data-status={status} dir={lang==='he'?'rtl':'ltr'}>
 <p className='small muted'>{material.id} · {index+1}/{questions.length}</p><h1>{question.translations[lang].title}</h1>
 <section id='reference' className='reference-solution'>{reference?<StudyText text={reference} solution/>:<p>Loading reference…</p>}</section>
 {resources&&<TechnicalMaterial material={material} lang={lang}/>}</main></>;
}createRoot(document.getElementById('root')).render(<Fixture/>);`;
  const bundle = await build({ stdin: { contents: source, loader: "tsx", sourcefile: "localization-fixture.tsx", resolveDir: web },
    bundle: true, write: false, platform: "browser", format: "iife", jsx: "automatic", minify: true,
    define: { "process.env.NODE_ENV": '"production"' } });
  const css = readFileSync(join(web, "src/app/ion.css"), "utf8") + readFileSync(join(web, "src/app/globals.css"), "utf8") +
    "body{font-family:Arial,sans-serif}nav{position:sticky;top:0;z-index:1;display:flex;flex-wrap:wrap;gap:6px;padding:12px;background:var(--paper);border-bottom:1px solid var(--line)}nav button{font-size:13px;padding:7px 12px}main{max-width:960px;margin:auto;padding:24px}h1{font-size:25px}.technical-material{margin-top:30px}.reference-solution{padding:20px;border:1px solid var(--line);border-radius:12px}.study-text{min-width:0}.study-text pre{overflow-x:auto}.technical-material dd{overflow-wrap:anywhere}@media(max-width:500px){main{padding:14px}h1{font-size:22px}.reference-solution{padding:14px}}";
  const html = "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Local question localization regression</title><link rel='stylesheet' href='/styles.css'></head><body><div id='root'></div><script src='/fixture.js'></script></body></html>";
  server = createServer((request, response) => {
    const path = new URL(request.url, "http://localhost").pathname;
    const asset = path === "/fixture.js" ? ["text/javascript", bundle.outputFiles[0].contents] :
      path === "/styles.css" ? ["text/css", css] : path === "/" ? ["text/html", html] : null;
    response.writeHead(asset ? 200 : 404, { "Content-Type": asset?.[0] ?? "text/plain", "Cache-Control": "no-store" });
    response.end(asset?.[1] ?? "Not found");
  });
  await new Promise(done => server.listen(0, "127.0.0.1", done));
  const origin = `http://127.0.0.1:${server.address().port}`;
  browser = spawn(edge, ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
    "--remote-debugging-port=0", `--user-data-dir=${join(fixture, "profile")}`, "about:blank"], { stdio: "ignore", windowsHide: true });
  browser.on("error", error => errors.push(error.message));
  let port;
  for (let i = 0; i < 100 && !port; i++) {
    await delay(100);
    try { port = Number(readFileSync(join(fixture, "profile/DevToolsActivePort"), "utf8").split("\n")[0]); } catch {}
  }
  if (!port) throw new Error(`Isolated Edge did not start: ${JSON.stringify(errors)}`);
  const target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(target => target.type === "page");
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((done, reject) => { ws.addEventListener("open", done, { once: true }); ws.addEventListener("error", reject, { once: true }); });
  ws.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) { pending.get(message.id)(message); pending.delete(message.id); }
    if (message.method === "Runtime.exceptionThrown") errors.push(message.params.exceptionDetails.exception?.description ?? message.params.exceptionDetails.text);
    if (message.method === "Network.requestWillBeSent" && !message.params.request.url.startsWith(origin)) errors.push(`Unexpected nonfixture request: ${message.params.request.url}`);
  });
  await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: origin });
  await waitFor("!!document.querySelector('main')", "fixture React mount");
  for (let i = 0; i < questions.length; i++) {
    const question = questions[i];
    await waitFor(`document.querySelector('main').dataset.key===${JSON.stringify(question.key)}`, question.key);
    await click("#he");
    const sections = await openSections();
    const hebrew = await facts();
    check(`${question.key}: Hebrew reference`, /\p{Script=Hebrew}/u.test(hebrew.reference));
    check(`${question.key}: sections open`, sections > 0 && hebrew.open === sections);
    await click("#en");
    const english = await facts();
    check(`${question.key}: English contents and headings`, !/\p{Script=Hebrew}/u.test(english.main));
    check(`${question.key}: sections stay open after language switch`, english.open === sections);
    check(`${question.key}: reference changed with language`, english.reference !== hebrew.reference && english.reference.length > 30);
    check(`${question.key}: English section labels`, english.summaries.every(label => !/\p{Script=Hebrew}/u.test(label)));
    await click("#pending");
    const waiting = await facts();
    check(`${question.key}: pending resources do not show Hebrew reference`, waiting.reference === "Loading reference…" && !/\p{Script=Hebrew}/u.test(waiting.main));
    await click("#legacy");
    const legacy = await facts();
    check(`${question.key}: legacy paired references stay English`, legacy.reference === english.reference && !/\p{Script=Hebrew}/u.test(legacy.main));
    await click("#he");
    const restored = await facts();
    check(`${question.key}: switching back restores Hebrew reference`, restored.reference === hebrew.reference);
    await click("#next");
    console.log(`CHECKED ${i + 1}/${questions.length} ${question.key}`);
  }
  for (const [device, width, height] of [["desktop", 1440, 1000], ["mobile", 390, 844]]) {
    await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: device === "mobile" });
    await send("Page.navigate", { url: `${origin}/?index=22` });
    await waitFor(`document.querySelector('main')?.dataset.key===${JSON.stringify(questions[22].key)}`, "power-of-two fixture");
    for (const lang of ["he", "en"]) {
      await click(`#${lang}`);
      await evaluate("scrollTo(0,0)");
      await screenshot(`${device}-${lang}-reference`);
      await openSections();
      await evaluate("scrollTo(0,document.querySelector('.technical-material').getBoundingClientRect().top+scrollY-document.querySelector('nav').offsetHeight-16)");
      await screenshot(`${device}-${lang}-technical`);
      const state = await facts();
      check(`${device}/${lang}: no page horizontal overflow`, !state.overflow);
      // Keep the next iteration's disclosure state deterministic.
      await evaluate("document.querySelectorAll('.technical-material > details').forEach(element=>element.open=false)");
    }
  }
} catch (error) {
  errors.push(error.stack ?? error.message);
} finally {
  const report = { started: new Date(started).toISOString(), seconds: (Date.now() - started) / 1000,
    questions: questions.length, passed: checks.filter(check => check.pass).length,
    failed: checks.filter(check => !check.pass).length, checks, screenshots, errors,
    scope: "Temporary fixture using the real study renderer and language helper. No application login or live API/database." };
  mkdirSync(out, { recursive: true });
  writeFileSync(join(out, "report.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({ ...report, checks: undefined }, null, 2));
  cleanup();
  if (errors.length || report.failed) process.exitCode = 1;
}
