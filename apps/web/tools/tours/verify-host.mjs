// Integration checks against an explicitly local screenshot-server fixture. Never calls the live API.
import { createRequire } from "node:module";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
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
  await page.goto(base, { waitUntil: "domcontentloaded" });
  const home = page.locator(".learn-head").getByRole("heading", { level: 1 });
  try { await home.waitFor({ timeout: 20000 }); }
  catch (error) { console.error((await page.locator("body").innerText()).slice(0, 1500)); throw error; }
  check(await page.locator("[data-muxi-station]").count() === 0, "A first authenticated visit shows the personal dashboard with the tour closed");
  const library = page.getByRole("link", { name: "מאגר", exact: true }).filter({ visible: true }).first();
  await library.click();
  await page.getByRole("textbox", { name: "חיפוש שאלות", exact: true }).fill("Intel");
  await page.getByRole("button", { name: "סיור עם מוקסי", exact: true }).click();
  check(await page.locator(".app-shell").evaluate(el => el.closest("[inert]") !== null), "Covered workspace is inert while its state stays mounted");
  await page.getByRole("button", { name: "דילוג ויציאה מהסיור", exact: true }).click();
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
  await page.getByRole("button", { name: "סיור עם מוקסי", exact: true }).click();
  await page.getByRole("button", { name: "מתחילים בסיור המעמיק", exact: true }).click();
  await page.getByRole("button", { name: "כל הפרקים", exact: true }).click();
  await page.getByRole("button", { name: "בונים ובודקים מעגל", exact: true }).click();
  await page.getByRole("button", { name: "הרחבת הלוח", exact: true }).click();
  await page.locator("dialog:modal [data-muxi-coach]").getByRole("button", { name: "יציאה ושמירת המקום", exact: true }).click();
  check(await explanation.inputValue() === "טיוטה שצריכה להישמר בזמן הסיור", "Exiting an expanded circuit tour preserves the unsent practice answer");
  check(await page.evaluate(() => document.body.style.overflow) !== "hidden", "Nested circuit and tour scroll locks release in either cleanup order");
  check(await page.locator("dialog:modal").count() === 0, "Expanded native dialog is removed on tour exit");
  await page.setViewportSize({ width: 390, height: 844 });
  check(await page.getByRole("button", { name: "סיור עם מוקסי", exact: true }).isVisible(), "Existing-user tour launcher remains available on mobile");
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), "Authenticated mobile header has no horizontal document overflow");
  await page.screenshot({ path: path.join(out, "host-mobile-launcher.png") });
  check(report.unexpectedRequests.length === 0, "All authenticated data requests stayed in the local fixture");
  check(report.errors.length === 0, "Authenticated tour integration has no uncaught browser errors");
  report.passed = true;
} catch (error) { report.error = String(error.stack || error); process.exitCode = 1; console.error(report.error); }
finally { await browser.close(); writeFileSync(path.join(out, "host-report.json"), JSON.stringify(report, null, 2)); }
