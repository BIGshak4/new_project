// Public preview. No real practice sessions, uploads, grades or account writes are allowed.
import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import assert from "node:assert/strict";
import { exerciseStation, nextStation, previewStations } from "./exercise-stations.mjs";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "C:/Users/harel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const base = process.argv[2] || "http://localhost:3214";
const out = path.resolve(process.argv[3] || "../../.impeccable/review/muxi/e2e");
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.EDGE_EXECUTABLE || "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", headless: true });
const report = { checks: [], pageErrors: [], forbiddenRequests: [], passed: false };
function check(condition, description) { assert.ok(condition, description); report.checks.push(description); }

async function verifyPreview({ width, height, lang, mobile }) {
  const context = await browser.newContext({ viewport: { width, height }, isMobile: mobile, hasTouch: mobile, reducedMotion: "reduce" });
  await context.addInitScript(language => {
    localStorage.setItem("jobrun-language", language);
    localStorage.setItem("jobrun-muxi-tour-v1-visitor", JSON.stringify({ version: 1, kind: "full", stepId: "goal", status: "paused" }));
    localStorage.setItem("jobrun-muxi-tour-v2-preview", JSON.stringify({ version: 2, kind: "preview", offered: true, stepId: "quiz", status: "paused" }));
  }, lang);
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  page.on("pageerror", e => report.pageErrors.push(e.message));
  page.on("request", r => {
    if (/\/v1\/(?:me|practice|interview|duel|evaluate)|supabase\.co\/(?:rest|storage|functions)|api\.(?:openai|anthropic)\.com/.test(r.url())) report.forbiddenRequests.push(r.method() + " " + r.url());
  });
  const area = station => page.locator(`[data-muxi-kind="preview"][data-muxi-station="${station}"]`);
  try {
    await page.goto(new URL("/", base).href, { waitUntil: "domcontentloaded" });
    const launcher = page.locator('a[aria-describedby="landing-tour-description"]');
    await launcher.waitFor();
    check(!await page.locator("[data-personal-helper]").count(), "A visitor sees the tour entry without the account helper");
    await launcher.click();
    await area("welcome").waitFor();
    await page.waitForFunction(lang => document.documentElement.lang === lang, lang);
    check(!await page.locator("[data-muxi-resume]").count(), "Old tour progress cannot resume an obsolete tour");
    await page.screenshot({ path: path.join(out, `preview-${lang}-welcome.png`) });
    await page.locator("[data-muxi-start]").click();
    for (const id of previewStations) {
      await area(id).waitFor();
      check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 2), `${lang}: ${id} fits the viewport`);
      const next = page.locator("[data-muxi-next]").filter({ visible: true }).first();
      check(await next.isDisabled(), `${lang}: ${id} opens with a task to try`);
      await exerciseStation(page, id);
      check(!await page.locator("[data-muxi-pointer],[data-personal-helper]").count(), `${lang}: ${id} leaves the exercise unobstructed`);
      await page.screenshot({ path: path.join(out, `preview-${lang}-${id}.png`) });
      await nextStation(page);
      if (id === "guest-library") {
        await area("guest-hardware").waitFor();
        await page.reload();
        await area("welcome").waitFor();
        await page.locator("[data-muxi-resume]").click();
        await area("guest-hardware").waitFor();
      }
    }
    await area("finish").waitFor();
    await area("finish").locator('a[href="/#signin"]').click();
    await page.waitForURL(url => url.pathname === "/" && url.hash === "#signin");
    check(true, `${lang}: every preview activity completes and ends at signup`);
  } catch (error) {
    await page.screenshot({ path: path.join(out, `failure-${lang}.png`) }).catch(() => {});
    console.error((await page.locator("body").innerText()).slice(-2500));
    throw error;
  } finally { await context.close(); }
}

try {
  await verifyPreview({ width: 1440, height: 960, lang: "he", mobile: false });
  await verifyPreview({ width: 390, height: 844, lang: "en", mobile: true });
  check(!report.forbiddenRequests.length, "No account, storage or model requests from the guest tour");
  check(!report.pageErrors.length, "No uncaught browser errors");
  report.passed = true;
} catch (error) {
  report.error = String(error.stack || error);
  console.error(report.error);
  process.exitCode = 1;
} finally {
  await browser.close();
  await fs.writeFile(path.join(out, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ passed: report.passed, checks: report.checks.length }));
}
