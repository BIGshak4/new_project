// Real-renderer regression: all 73 canonical questions, both translations, and
// independent browser glyph measurements for mixed-direction technical text.
// Run from apps/web: node tools/screenshots/bidi-localization.mjs
// The fixture binds loopback only and blocks every nonfixture network request.
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const web = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const outFlag = process.argv.indexOf("--out");
const out = resolve(outFlag < 0 ? join(web, "../../.impeccable/review/brackets") : process.argv[outFlag + 1]);
const require = createRequire(import.meta.url);
const runtimeModules = process.env.BIDI_NODE_MODULES ?? "C:/Users/harel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
function dependency(name) {
  try { return require(name); } catch { return require(join(runtimeModules, name)); }
}
const { build } = dependency("esbuild");
const { chromium } = dependency("playwright");
const edge = process.env.EDGE_PATH ?? "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const bankPaths = ["example_bank", "preparation_bank"].map(name => join(web, "../../backend/seeds/questions", `${name}.json`));
const bankBytes = bankPaths.map(path => readFileSync(path));
const bankHashes = bankBytes.map(bytes => createHash("sha256").update(bytes).digest("hex"));
const banks = bankBytes.map(bytes => JSON.parse(bytes.toString("utf8")));
const questions = banks.flat();
const entries = [];
function strings(value, path, question, lang) {
  if (typeof value === "string") entries.push({ id: entries.length, key: question.key, lang, path, text: value, solution: path === "reference_solution" });
  else if (value && typeof value === "object") for (const [key, child] of Object.entries(value)) strings(child, path ? `${path}.${key}` : key, question, lang);
}
for (const question of questions) for (const lang of ["he", "en"]) strings(question.translations[lang], "", question, lang);
if (banks[0].length !== 30 || banks[1].length !== 43 || entries.length !== 1330) throw new Error("Expected the 30 + 43 canonical questions and all 1,330 localized string fields.");

// These expected units are written independently of the segmentation helper.
// Browser Range rectangles check actual glyph placement, including both bracket
// endpoints and Markdown element boundaries, rather than retesting its output.
const specimens = [
  { id: "decoder", text: "האותות Y[3:0] ו־A[1:0] מחוברים.", units: ["Y[3:0]", "A[1:0]"] },
  { id: "nested", text: "יש לחשב fn(arr[i], {key: [1, 2]}) כעת.", units: ["fn(arr[i], {key: [1, 2]})"] },
  { id: "interval", text: "הטווח [lo,hi) הוא חצי פתוח.", units: ["[lo,hi)"] },
  { id: "pointer", text: "הגישה (*p)[i] חוקית.", units: ["(*p)[i]"] },
  { id: "math", text: "הביטוי (a[i] + b[j]) * (c - d) מחושב.", units: ["(a[i] + b[j])", "(c - d)"] },
  { id: "quotes", text: 'המונח "A[1:0]" נשמר.', units: ['"A[1:0]"'] },
  { id: "strong-boundary", text: "הפלט **Y[3:0**] מוכן.", units: ["Y[3:0]"] },
  { id: "emphasis-boundary", text: "הפלט A[*1:0*] מוכן.", units: ["A[1:0]"] },
  { id: "link-boundary", text: "הפלט [Y[3:0]](https://example.test) מוכן.", units: ["Y[3:0]"] },
  { id: "inline-code", text: "הפלט `Y[3:0]` מוכן.", units: ["Y[3:0]"], code: true },
  { id: "inline-code-boundary", text: "הפלט Y[`3:0`] מוכן.", units: ["Y[3:0]"] },
  { id: "inline-code-prefix", text: "הפלט `A`[1:0] מוכן.", units: ["A[1:0]"] },
  { id: "invalid-crossed", text: "הקלט ([)] שגוי.", literal: "([)]", units: ["([)]"] },
  { id: "invalid-close", text: "הקלט ] שגוי.", literal: "]", units: ["]"] },
  { id: "invalid-open", text: "הקלט (( שגוי.", literal: "((", units: ["(("] },
  { id: "brackets-only", text: "הקלט ([]{}) תקין.", literal: "([]{})", units: ["([]{})"] },
  { id: "quoted-invalid", text: 'הקלט "([)]" שגוי.', literal: '"([)]"', units: ['"([)]"'] },
  { id: "hebrew-prose", text: "משפט עברי (עם הערה בעברית) ממשיך כאן.", units: [] },
  { id: "english-prose", text: "English paragraph (with a bracketed note) ends here.", units: ["English paragraph (with a bracketed note) ends here."] },
  { id: "block-directions", text: "# English heading\n\nפסקה בעברית עם Y[3:0].\n\nEnglish paragraph with A[1:0].\n\n## כותרת בעברית\n\n- English list (first item).\n- פריט בעברית עם A[1:0].\n\n> English quotation (kept left to right).\n\n| English column | עמודה בעברית |\n| --- | --- |\n| A[1:0] | תא בעברית עם Y[3:0] |", units: [] },
  { id: "code-verbatim", text: "קוד נשאר ללא שינוי:\n\n```c\nint value = (*p)[i];\n// ([)] ] (( remain literal\nif (lo <= hi) { a[0] = value; }\n```", codeText: "int value = (*p)[i];\n// ([)] ] (( remain literal\nif (lo <= hi) { a[0] = value; }\n", units: [] },
];
const checks = [], screenshots = [], errors = [], requests = [], coverage = [];
const started = Date.now();
let browser, server;
function check(name, pass, detail) {
  checks.push({ name, pass: !!pass, ...(detail === undefined ? {} : { detail }) });
  if (!pass) console.error(`FAIL ${name}: ${JSON.stringify(detail)}`);
}

const source = `import React from 'react';
import {createRoot} from 'react-dom/client';
import {flushSync} from 'react-dom';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {StudyText,TechnicalMaterial} from './src/components/question-materials';
import {BidiText} from './src/components/bidi-text';
import {solutionMarkdown} from './src/lib/solution-markdown';
const entries=${JSON.stringify(entries)},questions=${JSON.stringify(questions)},specimens=${JSON.stringify(specimens)};
const root=createRoot(document.getElementById('root'));
function Plain({entry}) {return <div className="control" aria-hidden="true"><Markdown remarkPlugins={[remarkGfm]} skipHtml components={{img:({alt})=><span>{alt}</span>}}>{entry.solution?solutionMarkdown(entry.text):entry.text}</Markdown></div>}
function Pair({entry}) {return <><div className="actual"><StudyText text={entry.text} solution={entry.solution}/></div><Plain entry={entry}/></>}
function Fixture({view}) {
 if(view.mode==='corpus') return <main data-mode="corpus">{entries.slice(view.start,view.end).map(entry=><article key={entry.id} className="field" data-id={entry.id} data-language={entry.lang}><h2 className="field-label">{entry.key} · {entry.lang} · {entry.path}</h2><Pair entry={entry}/></article>)}</main>;
 if(view.mode==='specimens') return <main data-mode="specimens"><h1>{view.lang==='he'?'בדיקות תצוגת סוגריים':'Bracket rendering checks'}</h1><section className="specimens">{specimens.map(entry=><article key={entry.id} data-case={entry.id} className="field geometry"><h2 className="field-label">{entry.id}</h2><Pair entry={entry}/></article>)}</section></main>;
 const question=questions.find(question=>question.key===view.key),translation=question.translations[view.lang],material=question.assets.preparation_resource;
 return <main data-mode="question" data-key={question.key}><p className="field-label">{question.key}</p><h1><BidiText>{translation.title}</BidiText></h1><section className="question-prompt"><StudyText text={translation.prompt}/></section><section><StudyText text={translation.requirements}/></section><section><h2>{view.lang==='he'?'רמזים':'Hints'}</h2><ol>{translation.hints?.map((text,index)=><li key={index}><StudyText text={text}/></li>)}</ol></section><section className="reference-solution"><h2>{view.lang==='he'?'פתרון מוצע':'Reference solution'}</h2><StudyText text={translation.reference_solution} solution/></section>{material&&<TechnicalMaterial material={material} lang={view.lang}/>}</main>;
}
window.renderFixture=view=>{document.documentElement.dir=view.lang==='he'?'rtl':'ltr';document.documentElement.lang=view.lang;document.documentElement.dataset.theme=view.lang==='he'?'light':'dark';flushSync(()=>root.render(<Fixture view={view}/>));};
window.renderFixture({mode:'specimens',lang:'he'});
window.fixtureReady=true;`;

// This function is serialized into the browser. It does not import any product
// parser or direction helper, so expected text/direction stays independent.
function inspectFields() {
  const failures = [], fields = [...document.querySelectorAll(".field")];
  let blocks = 0, isolates = 0;
  const direction = text => {
    const letter = text.match(/[\p{L}\u200e\u200f]/u)?.[0];
    return letter && /[\p{Script=Hebrew}\p{Script=Arabic}\u200f]/u.test(letter) ? "rtl" : "ltr";
  };
  for (const field of fields) {
    const actual = field.querySelector(".actual .study-text"), control = field.querySelector(".control");
    const id = field.dataset.id ?? field.dataset.case;
    if (actual.textContent !== control.textContent) failures.push({ id, check: "literal text parity", actual: actual.textContent, expected: control.textContent });
    for (const block of actual.querySelectorAll("p,li,h1,h2,h3,h4,h5,h6,th,td,blockquote")) {
      if (!block.textContent.trim()) continue;
      blocks++;
      const expected = direction(block.textContent), computed = getComputedStyle(block).direction;
      if (computed !== expected) failures.push({ id, check: "source paragraph direction", tag: block.tagName, text: block.textContent.slice(0, 180), expected, computed });
    }
    for (const isolate of actual.querySelectorAll("bdi[dir=ltr]")) {
      isolates++;
      if (getComputedStyle(isolate).direction !== "ltr" || getComputedStyle(isolate).unicodeBidi !== "isolate") failures.push({ id, check: "LTR isolation computed style" });
    }
    for (const code of actual.querySelectorAll("pre,code")) {
      if (getComputedStyle(code).direction !== "ltr") failures.push({ id, check: "code direction" });
    }
  }
  return { fields: fields.length, blocks, isolates, failures };
}

function inspectSpecimens(expectedSpecimens) {
  const results = [];
  function textRange(element, needle) {
    const content = element.textContent, start = content.indexOf(needle);
    if (start < 0) return null;
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT), nodes = [];
    let node, offset = 0;
    while ((node = walker.nextNode())) { nodes.push({ node, start: offset, end: offset + node.textContent.length }); offset += node.textContent.length; }
    const point = index => {
      const position = nodes.find(part => index >= part.start && index < part.end) ?? nodes.at(-1);
      return [position.node, index - position.start];
    };
    const from = point(start), to = point(start + needle.length - 1), range = document.createRange();
    range.setStart(...from); range.setEnd(to[0], to[1] + 1);
    return { range, nodes, start, point };
  }
  for (const specimen of expectedSpecimens) {
    const element = document.querySelector(specimen.selector ?? ('[data-case="' + specimen.id + '"] .actual'));
    if (specimen.literal) results.push({ name: specimen.id + ': diagnostic bracket bytes stay literal', pass: element.textContent.includes(specimen.literal) });
    if (specimen.codeText) {
      const code = element.querySelector("pre code");
      results.push({ name: specimen.id + ': fenced code stays verbatim', pass: code?.textContent === specimen.codeText && !code?.querySelector("bdi"), detail: code?.textContent });
    }
    for (const unit of specimen.units) {
      const found = textRange(element, unit);
      if (!found) { results.push({ name: specimen.id + ': ' + unit, pass: false, detail: 'Expected literal unit missing' }); continue; }
      const ancestor = found.range.commonAncestorContainer.nodeType === Node.TEXT_NODE ? found.range.commonAncestorContainer.parentElement : found.range.commonAncestorContainer;
      const isolate = ancestor.closest(specimen.code ? 'code[dir="ltr"]' : 'bdi[dir="ltr"]');
      const whole = !!isolate && isolate.contains(found.range.startContainer) && isolate.contains(found.range.endContainer);
      const glyphs = [];
      for (let i = 0; i < unit.length; i++) {
        if (/\s/.test(unit[i])) continue;
        const point = found.point(found.start + i), glyph = document.createRange();
        glyph.setStart(...point); glyph.setEnd(point[0], point[1] + 1);
        const rect = glyph.getBoundingClientRect();
        glyphs.push({ char: unit[i], x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, width: rect.width });
      }
      const reversed = glyphs.filter((glyph, i) => i && Math.abs(glyph.y - glyphs[i - 1].y) < 2 && glyph.x <= glyphs[i - 1].x - 0.25);
      const rects = [...found.range.getClientRects()].map(rect => ({ x: rect.x, y: rect.y, width: rect.width, height: rect.height }));
      results.push({ name: specimen.id + ': complete LTR unit ' + unit, pass: whole && !reversed.length && glyphs.every(glyph => glyph.width > 0), detail: { whole, reversed, glyphs, rects } });
    }
  }
  return results;
}

async function render(page, view) {
  await page.evaluate(view => window.renderFixture(view), view);
  await page.evaluate(() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))));
}
async function shot(page, name, selector) {
  if (selector) await page.locator(selector).evaluate(element => scrollTo(0, element.getBoundingClientRect().top + scrollY - 16));
  else await page.evaluate(() => scrollTo(0, 0));
  await page.screenshot({ path: join(out, `${name}.png`), fullPage: false });
  screenshots.push(`${name}.png`);
}

try {
  mkdirSync(out, { recursive: true });
  const bundle = await build({ stdin: { contents: source, loader: "tsx", sourcefile: "bidi-localization-fixture.tsx", resolveDir: web },
    bundle: true, write: false, platform: "browser", format: "iife", jsx: "automatic", minify: true,
    define: { "process.env.NODE_ENV": '"production"' } });
  if (process.argv.includes("--build-only")) {
    console.log(JSON.stringify({ built: true, questions: questions.length, versions: questions.length * 2, fields: entries.length, bytes: bundle.outputFiles[0].contents.length }));
  } else {
    const css = readFileSync(join(web, "src/app/ion.css"), "utf8") + readFileSync(join(web, "src/app/globals.css"), "utf8") +
      "body{font-family:Arial,sans-serif}main{max-width:960px;margin:auto;padding:28px}h1{font-size:26px}.field{padding:15px 0;border-bottom:1px solid var(--line)}.field-label{font-size:12px;line-height:1.5;font-weight:500;direction:ltr;text-align:start;color:var(--muted)}.control{display:none}.geometry{font-size:16px}.specimens{display:grid;grid-template-columns:1fr 1fr;gap:12px 30px}.reference-solution{margin-top:24px;padding:18px;border:1px solid var(--line);border-radius:12px}.technical-material{margin-top:28px}.study-text{min-width:0}.study-text pre{overflow-x:auto}.technical-material dd{overflow-wrap:anywhere}@media(max-width:500px){main{padding:14px}h1{font-size:23px}.specimens{display:block}.reference-solution{padding:14px}.geometry{font-size:14px}}";
    const html = "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><link rel='icon' href='data:,'><title>Isolated bracket regression fixture</title><link rel='stylesheet' href='/styles.css'></head><body><div id='root'></div><script src='/fixture.js'></script></body></html>";
    server = createServer((request, response) => {
      const path = new URL(request.url, "http://localhost").pathname;
      const asset = path === "/fixture.js" ? ["text/javascript", bundle.outputFiles[0].contents] : path === "/styles.css" ? ["text/css", css] : path === "/" ? ["text/html", html] : null;
      response.writeHead(asset ? 200 : 404, { "Content-Type": asset?.[0] ?? "text/plain", "Cache-Control": "no-store" });
      response.end(asset?.[1] ?? "Not found");
    });
    await new Promise(done => server.listen(0, "127.0.0.1", done));
    const origin = `http://127.0.0.1:${server.address().port}`;
    browser = await chromium.launch({ executablePath: edge, headless: true });
    for (const [device, width, height] of [["desktop", 1440, 1000], ["mobile", 390, 844]]) {
      for (const lang of ["he", "en"]) {
        const environment = `${device}-${lang}-${lang === "he" ? "light" : "dark"}`;
        const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, isMobile: device === "mobile", reducedMotion: "reduce" });
        await context.route("**/*", route => {
          const url = route.request().url(), allowed = url.startsWith(origin + "/") && ["/", "/styles.css", "/fixture.js"].includes(new URL(url).pathname);
          requests.push({ environment, url, allowed });
          if (!allowed) { errors.push(`Blocked unexpected request: ${url}`); return route.abort(); }
          return route.continue();
        });
        const page = await context.newPage();
        page.on("pageerror", error => errors.push(`${environment}: ${error.message}`));
        await page.goto(origin);
        await page.waitForFunction(() => window.fixtureReady);
        const counts = { environment, fields: 0, blocks: 0, isolates: 0, batches: 0, questionVersions: new Set() };
        for (let start = 0; start < entries.length; start += 80) {
          const end = Math.min(start + 80, entries.length);
          await render(page, { mode: "corpus", lang, start, end });
          const result = await page.evaluate(inspectFields);
          counts.fields += result.fields; counts.blocks += result.blocks; counts.isolates += result.isolates; counts.batches++;
          for (const entry of entries.slice(start, end)) counts.questionVersions.add(`${entry.key}:${entry.lang}`);
          check(`${environment}: fields ${start + 1}–${end} preserve Markdown text and source direction`, result.fields === end - start && !result.failures.length, result.failures.length ? result.failures : undefined);
        }
        check(`${environment}: complete canonical corpus`, counts.fields === 1330 && counts.questionVersions.size === 146, { fields: counts.fields, versions: counts.questionVersions.size, blocks: counts.blocks, isolates: counts.isolates });
        coverage.push({ ...counts, questionVersions: counts.questionVersions.size });
        await render(page, { mode: "specimens", lang });
        const specimenFields = await page.evaluate(inspectFields);
        check(`${environment}: independent Markdown specimens preserve text and block direction`, !specimenFields.failures.length, specimenFields.failures.length ? specimenFields.failures : undefined);
        for (const result of await page.evaluate(inspectSpecimens, specimens)) check(`${environment}: ${result.name}`, result.pass, result.detail);
        await shot(page, `${environment}-technical-examples`);
        if (device === "mobile") await shot(page, `${environment}-markdown-boundaries`, '[data-case="strong-boundary"]');
        await render(page, { mode: "question", lang, key: "example-enabled-decoder" });
        check(`${environment}: decoder includes complete vector literals`, await page.locator("main").evaluate(main => main.textContent.includes("Y[3:0]") && main.textContent.includes("A[1:0]")));
        for (const result of await page.evaluate(inspectSpecimens, [{ id: "canonical decoder prompt", selector: ".question-prompt", units: ["Y[3:0]", "A[1:0]"] }])) check(`${environment}: ${result.name}`, result.pass, result.detail);
        check(`${environment}: decoder does not overflow viewport`, await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
        await shot(page, `${environment}-decoder`);
        await render(page, { mode: "question", lang, key: "prep-isolate-highest-one-eight-bits" });
        await page.locator(".technical-material > details").evaluateAll(details => details.forEach(detail => { detail.open = true; }));
        check(`${environment}: real technical disclosures render`, await page.locator(".technical-material > details[open]").count() > 0);
        check(`${environment}: technical material does not overflow viewport`, await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
        await shot(page, `${environment}-technical-material`, ".technical-material");
        await context.close();
        console.log(`CHECKED ${environment}: ${counts.fields} fields, ${counts.questionVersions.size} versions, ${counts.blocks} blocks`);
      }
    }
    check("No API, database, external, or nonfixture HTTP requests", requests.every(request => request.allowed), { requests: requests.length, blocked: requests.filter(request => !request.allowed).length });
  }
  check("Canonical question source bytes are unchanged", bankPaths.every((path, i) => createHash("sha256").update(readFileSync(path)).digest("hex") === bankHashes[i]), bankHashes);
} catch (error) {
  errors.push(error.stack ?? error.message);
} finally {
  await browser?.close();
  await new Promise(done => server ? server.close(done) : done());
  const report = { started: new Date(started).toISOString(), seconds: (Date.now() - started) / 1000, questions: questions.length, versions: 146, localizedStringFields: entries.length,
    passed: checks.filter(check => check.pass).length, failed: checks.filter(check => !check.pass).length, coverage, checks, screenshots, errors, requests,
    scope: "Actual StudyText, BidiText and TechnicalMaterial bundled from source, compared with an unsegmented Markdown control and handwritten Range/glyph expectations. Fresh isolated headless Edge contexts; loopback fixture only; no accounts or API/database access." };
  mkdirSync(out, { recursive: true });
  writeFileSync(join(out, "report.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({ ...report, checks: undefined, requests: undefined }, null, 2));
  if (errors.length || report.failed) process.exitCode = 1;
}
