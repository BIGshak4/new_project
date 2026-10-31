// Interactive renderer checks with a deliberately deferred API double.
// This verifies UI behavior, never claims to execute submitted source or contact a real executor.
import { createServer } from "node:http";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const web = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const out = resolve(web, "../../.impeccable/execution-20261031/frontend");
const require = createRequire(import.meta.url);
const dependencies = process.env.CODEX_NODE_MODULES ?? "C:/Users/harel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const dependency = (name) => { try { return require(name); } catch { return require(join(dependencies, name)); } };
const { build } = dependency("esbuild"), { chromium } = dependency("playwright");
const source = `
import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import {CodeExecutionPanel} from './src/components/code-execution-panel';
window.fixtureCalls=[]; window.pending=[];
const capabilities={available:true,languages:['python','javascript','c','cpp','verilog','systemverilog','vhdl'],tested_languages:['python'],contract:{he:'ממשו answer(n). הפונקציה מחזירה את n ועוד 1.',en:'Implement answer(n), returning n plus 1.'},starters:{python:'def answer(n):\\n    return n + 1'}};
const api={executionCapabilities:async()=>({...capabilities,available:window.fixtureAvailable!==false}),executeCode:async(id,body,signal)=>{window.fixtureCalls.push({id,body}); return new Promise((resolve,reject)=>window.pending.push({resolve,reject}));}};
const root=createRoot(document.getElementById('root'));
function Fixture({lang}){
 const [source,setSource]=useState(''),[language,setLanguage]=useState('python');
 return <main><h1>{lang==='he'?'בדיקת ממשק הרצת קוד':'Code execution UI fixture'}</h1><label>Source<textarea aria-label="Fixture source" value={source} onChange={e=>setSource(e.target.value)}/></label><label>Language<select aria-label="Fixture language" value={language} onChange={e=>setLanguage(e.target.value)}>{capabilities.languages.map(l=><option key={l}>{l}</option>)}</select></label><CodeExecutionPanel context={{attemptId:'fixture-owned',api}} language={language} source={source} lang={lang} disabled={false} onUseStarter={setSource}/></main>
}
window.renderFixture=(lang)=>{document.documentElement.lang=lang;document.documentElement.dir=lang==='he'?'rtl':'ltr';document.documentElement.dataset.theme=lang==='he'?'light':'dark';root.render(<Fixture key={lang+String(window.fixtureAvailable)} lang={lang}/>)};
window.fixtureResult=(patch={})=>({status:'completed',language:'c',compiled:true,executed:true,passed:null,stdout:'',stderr:'',compile_output:'',cases:[],runtime_ms:27,detail:'',...patch});
window.renderFixture('en');
`;
const bundle = await build({ stdin: { contents: source, loader: "tsx", sourcefile: "execution-fixture.tsx", resolveDir: web }, bundle: true, write: false, outdir: "fixture", platform: "browser", format: "iife", jsx: "automatic", minify: true, define: { "process.env.NODE_ENV": '"production"' } });
const script = bundle.outputFiles.find((file) => file.path.endsWith(".js")).contents;
const moduleCss = bundle.outputFiles.find((file) => file.path.endsWith(".css"))?.text ?? "";
const css = readFileSync(join(web, "src/app/ion.css"), "utf8") + readFileSync(join(web, "src/app/globals.css"), "utf8") + moduleCss + "body{font-family:Arial,sans-serif}main{max-width:900px;margin:auto;padding:24px}h1{font-size:24px;margin-bottom:20px}main>label{margin-block:12px}main>label>textarea{min-height:70px}@media(max-width:500px){main{padding:14px}}";
const html = "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><link rel='icon' href='data:,'><link rel='stylesheet' href='/style.css'><title>Execution UI fixture</title></head><body><div id='root'></div><script src='/fixture.js'></script></body></html>";
const server = createServer((request, response) => {
  const path = new URL(request.url, "http://localhost").pathname;
  const asset = path === "/" ? ["text/html", html] : path === "/style.css" ? ["text/css", css] : path === "/fixture.js" ? ["text/javascript", script] : null;
  response.writeHead(asset ? 200 : 404, { "Content-Type": asset?.[0] ?? "text/plain" }); response.end(asset?.[1] ?? "Not found");
});
let browser;
const checks = [], errors = [];
const check = (name, pass, details) => { checks.push({ name, pass, ...(details === undefined ? {} : { details }) }); if (!pass) throw new Error(name); };
try {
  mkdirSync(out, { recursive: true });
  await new Promise((done) => server.listen(0, "127.0.0.1", done));
  const origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({ executablePath: process.env.EDGE_PATH ?? "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", headless: true });
  for (const width of [1360, 390]) for (const lang of ["he", "en"]) {
    const name = `${width}-${lang}`, context = await browser.newContext({ viewport: { width, height: 960 }, reducedMotion: "reduce" });
    await context.route("**/*", (route) => route.request().url().startsWith(origin + "/") ? route.continue() : route.abort());
    const page = await context.newPage(); page.on("pageerror", (error) => errors.push(`${name}: ${error.message}`));
    await page.goto(origin); await page.waitForFunction(() => typeof window.renderFixture === "function");
    await page.evaluate((lang) => window.renderFixture(lang), lang);
    const panel = page.getByRole("region", { name: lang === "he" ? "הרצת קוד" : "Code execution" });
    await panel.getByRole("button", { name: lang === "he" ? "טעינת שלד קוד לבדיקה" : "Load a test-ready starter" }).click();
    check(`${name}: starter loads only by explicit action`, (await page.getByLabel("Fixture source").inputValue()).includes("def answer(n)"));
    await panel.getByRole("button", { name: lang === "he" ? "הרצה מול בדיקות השאלה" : "Run question tests" }).click();
    await page.waitForFunction(() => window.pending.length === 1);
    await page.getByLabel("Fixture source").fill("def answer(n): return n + 2");
    await page.evaluate(() => window.pending.shift().resolve(window.fixtureResult({ status: "passed", passed: true })));
    await page.waitForTimeout(80);
    check(`${name}: edited draft discards a late passed response`, await panel.locator('[data-execution-status="passed"]').count() === 0);
    await panel.getByRole("button", { name: lang === "he" ? "הרצה מול בדיקות השאלה" : "Run question tests" }).click();
    await page.waitForFunction(() => window.pending.length === 1);
    await page.evaluate(() => window.pending.shift().resolve(window.fixtureResult({ status: "passed", passed: true, cases: [{ index: 0, passed: true, input: [1], expected: 2, actual: 2 }] })));
    await panel.locator('[data-execution-status="passed"]').waitFor();
    check(`${name}: server-tested result appears`, await panel.getByText(lang === "he" ? "כל הבדיקות שהוגדרו עברו" : "All configured tests passed", { exact: true }).count() === 1);
    await page.getByLabel("Fixture source").fill("edited draft");
    check(`${name}: prior result is marked stale`, (await panel.innerText()).includes(lang === "he" ? "שייכת לגרסה הקודמת" : "previous version"));
    await page.getByLabel("Fixture language").selectOption("c");
    await panel.locator("details").first().locator("summary").click();
    await panel.getByLabel(lang === "he" ? "טקסט שיועבר לתוכנית בזמן ההרצה" : "Text passed to the program during execution").fill("123\n");
    await panel.getByRole("button", { name: lang === "he" ? "הרצת הקוד" : "Run code", exact: true }).click();
    await page.waitForFunction(() => window.pending.length === 1);
    await page.evaluate(() => window.pending.shift().resolve(window.fixtureResult({ stdout: '<img src=x onerror="bad()"><script>bad()</script>\n' + 'x'.repeat(700) })));
    await panel.locator('[data-execution-status="completed"]').waitFor();
    check(`${name}: stdin is sent without client tests`, await page.evaluate(() => { const body = window.fixtureCalls.at(-1).body; return body.stdin === "123\n" && !Object.hasOwn(body, "cases") && !Object.hasOwn(body, "spec"); }));
    check(`${name}: complete is explicitly unassessed`, (await panel.innerText()).includes(lang === "he" ? "נכונות: לא נבדקה" : "Correctness: not assessed"));
    check(`${name}: output never becomes HTML`, await panel.locator("img,script").count() === 0);
    const overflow = await page.evaluate(() => ({ width: innerWidth, content: document.documentElement.scrollWidth }));
    check(`${name}: page stays inside viewport with long output`, overflow.content <= overflow.width, overflow);
    await page.screenshot({ path: join(out, `${name}-output.png`), fullPage: true });
    await panel.getByRole("button", { name: lang === "he" ? "הרצת הקוד" : "Run code", exact: true }).click();
    await page.waitForFunction(() => window.pending.length === 1);
    await page.evaluate(() => window.pending.shift().reject({ status: 429 }));
    await panel.getByRole("alert").waitFor();
    check(`${name}: quota message gives recovery`, (await panel.getByRole("alert").innerText()).includes(lang === "he" ? "מגבלת ההרצות" : "execution limit"));
    await panel.getByRole("button", { name: lang === "he" ? "הרצת הקוד" : "Run code", exact: true }).click();
    await page.waitForFunction(() => window.pending.length === 1);
    await panel.getByRole("button", { name: lang === "he" ? "הפסקת המתנה" : "Stop waiting" }).click();
    await page.evaluate(() => window.pending.shift().resolve(window.fixtureResult({ stdout: "cancelled late response" })));
    await page.waitForTimeout(50);
    check(`${name}: cancel ignores transport-late response`, !(await panel.innerText()).includes("cancelled late response"));
    await page.evaluate((lang) => { window.fixtureAvailable = false; window.renderFixture(lang); }, lang);
    await panel.getByText(lang === "he" ? /שירות ההרצה אינו זמין/ : /Execution is currently unavailable/).waitFor();
    check(`${name}: provider unavailable offers availability retry without a fake run`, await panel.getByRole("button", { name: lang === "he" ? "בדיקת זמינות מחדש" : "Check availability again" }).count() === 1 && await panel.locator('[data-muxi-control="code-execute"]').count() === 0);
    await context.close();
  }
  check("No browser JavaScript errors", errors.length === 0, errors);
} finally {
  await browser?.close(); await new Promise((done) => server.close(done));
  writeFileSync(join(out, "browser-ui-verification.json"), JSON.stringify({ fixture: "Deferred API double; no user code execution or live account", checks, errors, passed: checks.every((check) => check.pass) && !errors.length }, null, 2));
}
console.log(JSON.stringify({ passed: checks.length, errors: errors.length, evidence: out }));
