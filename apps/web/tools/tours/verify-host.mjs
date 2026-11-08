// Integration checks against an explicitly local screenshot-server fixture. Never calls the live API.
import { createRequire } from "node:module";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { exerciseStation, memberStations, nextStation, tourControl } from "./exercise-stations.mjs";
const require = createRequire(process.env.PLAYWRIGHT_PACKAGE_ROOT || "C:/Users/harel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json");
const { chromium } = require("playwright");
const base = process.argv[2] || "http://localhost:3212";
const fixturePath = process.argv[3];
if (!fixturePath || !["localhost", "127.0.0.1"].includes(new URL(base).hostname)) throw Error("Provide a local app URL and local screenshot-server session file");
const fixture = JSON.parse(readFileSync(fixturePath, "utf8"));
for (const url of [fixture.api, fixture.stub]) if (!["localhost", "127.0.0.1"].includes(new URL(url).hostname)) throw Error("Fixture endpoints must be local");
const out = path.dirname(fixturePath);
mkdirSync(out, { recursive: true });
const publicEnv = readFileSync(path.resolve(".env.local"), "utf8");
const supaUrl = publicEnv.match(/^NEXT_PUBLIC_SUPABASE_URL=["']?([^\r\n"']+)/m)?.[1];
const report = { checks: [], unexpectedRequests: [], errors: [], passed: false };
const check = (condition, description) => { assert.ok(condition, description); report.checks.push(description); console.log("PASS", description); };
const browser = await chromium.launch({ executablePath: process.env.EDGE_PATH || "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  await context.route("**/*", async route => {
    const request = route.request(), url = new URL(request.url());
    let endpoint;
    if (/^\/(?:auth|rest|storage)\/v1\//.test(url.pathname)) endpoint = fixture.stub;
    else if (/^\/v1\//.test(url.pathname) || url.pathname === "/health") endpoint = fixture.api;
    if (endpoint) {
      const response = await route.fetch({ url: endpoint + url.pathname + url.search });
      await route.fulfill({ response });
    } else if (url.origin === new URL(base).origin || url.protocol === "data:" || url.protocol === "blob:") await route.continue();
    else { report.unexpectedRequests.push(url.origin + url.pathname); await route.abort(); }
  });
  await context.addInitScript(({ session, supa }) => {
    for (const host of ["localhost", "127", ...(supa ? [new URL(supa).hostname.split(".")[0]] : [])]) localStorage.setItem(`sb-${host}-auth-token`, JSON.stringify(session));
  }, { session: fixture.session, supa: supaUrl });
  const page = await context.newPage();
  page.on("pageerror", error => report.errors.push(error.message));
  const helper = page.locator("[data-personal-helper] > button");
  async function checkHelperAvailable(description) {
    await helper.click({ trial: true });
    check(await helper.isVisible(), description);
  }
  await page.goto(base, { waitUntil: "domcontentloaded" });
  const home = page.locator(".learn-head").getByRole("heading", { level: 1 });
  try { await home.waitFor({ timeout: 20000 }); }
  catch (error) { console.error((await page.locator("body").innerText()).slice(0, 1500)); throw error; }
  check(await page.locator("[data-muxi-station]").count() === 0, "A first authenticated visit shows the personal dashboard with the tour closed");
  await checkHelperAvailable("The personal helper is reachable on the dashboard after the entry splash");
  await page.locator("[data-jobrun-inbox-trigger]").filter({ visible: true }).first().click();
  const inbox = page.locator("dialog[data-jobrun-inbox-dialog]:modal");
  await inbox.waitFor();
  check(await helper.isHidden(), "An open updates dialog hides the underlying helper");
  await inbox.getByRole("button", { name: "סגירת עדכונים ופניות", exact: true }).click();
  await checkHelperAvailable("Closing the updates dialog automatically restores the helper");
  const library = page.getByRole("link", { name: "מאגר", exact: true }).filter({ visible: true }).first();
  await library.click();
  await page.getByRole("textbox", { name: "חיפוש שאלות", exact: true }).fill("Intel");
  await page.getByRole("button", { name: "סיור עם מוקסי", exact: true }).click();
  check(await page.locator(".app-shell").evaluate(el => el.closest("[inert]") !== null), "Covered workspace is inert while its state stays mounted");
  check(await helper.isHidden(), "The helper is hidden during the tour");
  await page.locator("[data-muxi-station] header").getByRole("button", { name: "יציאה מהסיור", exact: true }).click();
  await checkHelperAvailable("Exiting the tour restores the helper in the library");
  check(await page.getByRole("textbox", { name: "חיפוש שאלות", exact: true }).inputValue() === "Intel", "Closing a replayed tour preserves the real library search");
  check(await page.evaluate(() => document.body.style.overflow) !== "hidden", "Closing restores document scrolling");
  await page.reload({ waitUntil: "domcontentloaded" });
  await home.waitFor();
  check(await page.locator("[data-muxi-station]").count() === 0, "Reload returns to the dashboard without reopening the tour");
  for (const path of ["/?view=library&question=example-sensor-majority", "/games/shop"]) {
    await page.goto(base + path, { waitUntil: "domcontentloaded" });
    await home.waitFor();
    check(new URL(page.url()).pathname + new URL(page.url()).search === "/", `A fresh visit to ${path} opens the dashboard`);
  }
  const shop = page.getByRole("link", { name: "החנות של מוקסי", exact: true }).filter({ visible: true }).first();
  await shop.click();
  await page.locator('a[aria-current="page"]').getByText("החנות של מוקסי", { exact: true }).first().waitFor();
  check(new URL(page.url()).pathname === "/games/shop", "Selecting the shop in the dashboard opens the real shop");
  await page.goBack();
  await home.waitFor();
  check(new URL(page.url()).pathname === "/", "Browser Back from the shop restores the dashboard");
  await page.getByRole("button", { name: "פתיחת העוזר האישי", exact: true }).click();
  await page.getByRole("button", { name: "הדמות שלי והמשחקים", exact: true }).click();
  await page.getByRole("button", { name: "איך משנים את הדמות?", exact: true }).click();
  const newPage = context.waitForEvent("page");
  await page.getByRole("link", { name: "פתיחת החנות של מוקסי" }).click();
  const helperShop = await newPage;
  await helperShop.locator('a[aria-current="page"]').getByText("החנות של מוקסי", { exact: true }).first().waitFor();
  check(new URL(helperShop.url()).pathname === "/games/shop", "The helper can open the real shop in a new tab");
  await helperShop.close();
  await page.getByRole("button", { name: "מזעור העוזר", exact: true }).click();
  await library.click();
  await page.getByRole("button", { name: "הכרעת רוב בין שלושה חיישנים", exact: true }).click();
  await page.getByRole("button", { name: "כתיבת פתרון", exact: true }).click();
  await page.getByRole("button", { name: "כתיבת הסבר לפתרון", exact: true }).click();
  const explanation = page.getByRole("textbox", { name: "הסבר הפתרון", exact: true });
  await explanation.fill("טיוטה שצריכה להישמר בזמן הסיור");
  await page.locator('[data-muxi-control="circuit-open"]').click();
  const inlineCircuit = page.locator('dialog[open][data-layout="inline"]');
  await inlineCircuit.waitFor();
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    await checkHelperAvailable(`An inline circuit keeps the helper reachable at ${viewport.width}px`);
    await helper.click();
    const minimize = page.getByRole("button", { name: "מזעור העוזר", exact: true });
    await minimize.click();
    await inlineCircuit.locator('[data-muxi-control="circuit-fullscreen"]').click();
    const fullCircuit = page.locator('dialog:modal[data-layout="fullscreen"]');
    await fullCircuit.waitFor();
    check(await helper.isHidden(), `The full-screen circuit hides the underlying helper at ${viewport.width}px`);
    await fullCircuit.locator('[data-muxi-control="circuit-expand"]').click();
    await inlineCircuit.waitFor();
    await checkHelperAvailable(`Returning to the inline circuit automatically restores the helper at ${viewport.width}px`);
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole("button", { name: "סיור עם מוקסי", exact: true }).click();
  const writes = [];
  const captureWrite = request => {
    const { pathname } = new URL(request.url());
    if (request.method() === "POST" && pathname.startsWith("/v1/")) writes.push(pathname);
  };
  page.on("request", captureWrite);
  const tour = page.locator('[data-muxi-kind="member"]');
  await tour.locator("[data-muxi-start]").click();
  const stage = tour.locator("[data-muxi-stage]");
  await stage.locator('form, [data-muxi-control="goal-keep"]').first().waitFor();
  if (await tourControl(page, "goal-keep").isVisible()) await stage.getByRole("button", { name: "עריכת היעד" }).click();
  check(!writes.length, "Opening the member tour reads the current plan without writing defaults");
  await stage.locator('[data-goal-section="roles"] summary').click();
  await stage.locator('[data-goal-section="roles"] input[type="checkbox"]').first().check();
  await stage.locator('[data-goal-section="minutes"] summary').click();
  await stage.locator('[data-goal-section="minutes"]').getByRole("radio", { name: /45/ }).check();
  const saved = page.waitForResponse(r => new URL(r.url()).pathname === "/v1/me/goal" && r.request().method() === "POST");
  await tourControl(page, "goal-save").click();
  const savedResponse = await saved;
  check(savedResponse.ok() && (await savedResponse.json()).minutes_per_day === 45, "Explicit confirmation saves the actual plan through the account API");
  await nextStation(page);
  for (const id of memberStations.slice(1)) {
    await page.locator(`[data-muxi-station="${id}"]`).waitFor();
    await exerciseStation(page, id);
    await nextStation(page);
  }
  await page.locator('[data-muxi-station="finish"]').waitFor();
  await tour.getByRole("button", { name: "חזרה לאתר", exact: true }).click();
  check(await explanation.inputValue() === "טיוטה שצריכה להישמר בזמן הסיור", "Completing the member tour preserves the unsent practice answer");
  check(await page.evaluate(() => document.body.style.overflow) !== "hidden", "Exiting the tour restores document scrolling");
  await page.getByRole("link", { name: "אזור אישי", exact: true }).filter({ visible: true }).first().click();
  await home.waitFor();
  check((await page.locator("[data-goal-summary]").first().innerText()).includes("45"), "The dashboard reflects the newly saved goal");
  await page.getByRole("button", { name: "סיור עם מוקסי", exact: true }).click();
  await tour.locator("[data-muxi-start]").click();
  await tourControl(page, "goal-keep").click();
  await nextStation(page);
  await tour.getByRole("button", { name: "כל התחנות" }).click();
  await tour.locator('[data-muxi-stop="circuit"]').click();
  await tourControl(page, "circuit-editor-details").click();
  await tourControl(page, "circuit-expand").click();
  await page.locator("dialog:modal [data-muxi-coach]").getByRole("button", { name: "יציאה ושמירת המקום", exact: true }).click();
  check(await page.locator("dialog:modal").count() === 0, "Exiting an expanded tour circuit releases the native modal");
  check(writes.length === 1 && writes[0] === "/v1/me/goal", "Replaying, keeping an existing goal and trying examples do not create extra practice records");
  page.off("request", captureWrite);
  await page.setViewportSize({ width: 390, height: 844 });
  check(await page.getByRole("button", { name: "סיור עם מוקסי", exact: true }).isVisible(), "Existing-user tour launcher remains available on mobile");
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), "Authenticated mobile header has no horizontal document overflow");
  await page.screenshot({ path: path.join(out, "host-mobile-launcher.png") });
  check(report.unexpectedRequests.length === 0, "All authenticated data requests stayed in the local fixture");
  check(report.errors.length === 0, "Authenticated tour integration has no uncaught browser errors");
  report.passed = true;
} catch (error) { report.error = String(error.stack || error); process.exitCode = 1; console.error(report.error); }
finally { await browser.close(); writeFileSync(path.join(out, "host-report.json"), JSON.stringify(report, null, 2)); }
