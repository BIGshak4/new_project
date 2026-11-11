// Real approved game-bank requests against the local screenshot-server fixture only.
import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(process.env.PLAYWRIGHT_PACKAGE_ROOT || "C:/Users/harel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json");
const { chromium } = require("playwright");
const base = process.argv[2];
const fixturePath = process.argv[3];
const local = value => ["localhost", "127.0.0.1"].includes(new URL(value).hostname);
if (!base || !fixturePath || !local(base)) throw Error("Provide a local app URL and screenshot-server session file");
const fixture = JSON.parse(readFileSync(fixturePath, "utf8"));
if (![fixture.api, fixture.stub].every(local)) throw Error("Only local fixtures are allowed");
const publicEnv = readFileSync(path.resolve(".env.local"), "utf8");
const supaUrl = publicEnv.match(/^NEXT_PUBLIC_SUPABASE_URL=["']?([^\r\n"']+)/m)?.[1];
const bank = JSON.parse(readFileSync(path.resolve("../../backend/seeds/duel_quiz.json"), "utf8")).questions;
const out = path.dirname(fixturePath);
const report = { checks: [], unexpectedRequests: [], errors: [], passed: false };
const check = (condition, message) => { assert.ok(condition, message); report.checks.push(message); console.log("PASS", message); };
const browser = await chromium.launch({ executablePath: process.env.EDGE_PATH || "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", headless: true });
try {
  for (const config of [{ width: 1440, height: 1000, lang: "he", theme: "light", correct: true }, { width: 390, height: 844, lang: "en", theme: "dark", correct: false }]) {
    const context = await browser.newContext({ viewport: { width: config.width, height: config.height } });
    const mutations = [];
    await context.route("**/*", async route => {
      const request = route.request(), url = new URL(request.url());
      let endpoint;
      if (/^\/(?:auth|rest|storage)\/v1\//.test(url.pathname)) endpoint = fixture.stub;
      else if (/^\/v1\//.test(url.pathname) || url.pathname === "/health") endpoint = fixture.api;
      if (request.method() === "POST" && url.pathname.startsWith("/v1/duels")) mutations.push(url.pathname);
      if (endpoint) {
        const response = await route.fetch({ url: endpoint + url.pathname + url.search });
        await route.fulfill({ response });
      } else if (url.origin === new URL(base).origin || ["data:", "blob:"].includes(url.protocol)) await route.continue();
      else { report.unexpectedRequests.push(url.origin + url.pathname); await route.abort(); }
    });
    await context.addInitScript(({ session, supa, lang, theme }) => {
      for (const host of ["localhost", "127", ...(supa ? [new URL(supa).hostname.split(".")[0]] : [])]) localStorage.setItem(`sb-${host}-auth-token`, JSON.stringify(session));
      localStorage.setItem("jobrun-language", lang);
      localStorage.setItem("jobrun-theme", theme);
    }, { session: fixture.session, supa: supaUrl, lang: config.lang, theme: config.theme });
    const page = await context.newPage();
    page.on("pageerror", error => report.errors.push(error.message));
    // Fresh account entry intentionally lands on the personal area. Follow its real games link.
    await page.goto(base, { waitUntil: "domcontentloaded" });
    await page.locator('a[href="/games"]:visible').first().click();
    const practice = page.locator('[data-member-tour="game-practice"]');
    await practice.waitFor({ timeout: 30000 });
    check(await page.locator('[data-member-tour="game-invite"]').count() === 1, "The real invitation control has its tour anchor");
    const questionResponse = page.waitForResponse(response => new URL(response.url()).pathname === "/v1/duels/practice" && response.ok());
    await practice.locator('[data-member-tour="game-practice-start"]').click();
    const round = await (await questionResponse).json();
    const source = bank.find(question => question.key === round.question.key);
    check(source?.status === "approved" && source.prompt[config.lang] === round.question.prompt,
      `${config.lang}: the question is an approved question from the production game bank`);
    check(!("correct" in round.question) && !("explanation" in round.question), "The first response contains no answer or explanation");
    const choices = practice.locator('[data-member-tour="game-practice-choice"]');
    await choices.last().waitFor();
    check(await choices.count() === 4, "All four actual bank choices are rendered");
    check(await practice.locator('[data-member-tour="game-practice-check"]').isDisabled(), "An answer must be selected before checking");
    await choices.nth(config.correct ? source.correct : (source.correct + 1) % 4).check();
    const answerResponse = page.waitForResponse(response => new URL(response.url()).pathname === "/v1/duels/practice/answer" && response.ok());
    await practice.locator('[data-member-tour="game-practice-check"]').click();
    const answer = await (await answerResponse).json();
    check(answer.correct === config.correct && answer.correct_index === source.correct && answer.explanation === source.explanation[config.lang], "The real server checks the selected answer and returns the bank explanation");
    await practice.locator('[data-member-tour="game-practice-result"]').waitFor();
    check(await choices.first().isDisabled(), "Checked answers are locked while their explanation is shown");
    await practice.scrollIntoViewIfNeeded();
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${config.width}px ${config.theme} game practice fits the screen`);
    await practice.screenshot({ path: path.join(out, `member-game-${config.width}-${config.theme}.png`) });
    const nextResponse = page.waitForResponse(response => new URL(response.url()).pathname === "/v1/duels/practice" && response.ok());
    await practice.locator('[data-member-tour="game-practice-start"]').click();
    await nextResponse;
    await practice.locator('[data-member-tour="game-practice-check"]').waitFor();
    check(await practice.locator('[data-member-tour="game-practice-result"]').count() === 0 && await practice.locator('[data-member-tour="game-practice-check"]').isDisabled(), "A new round removes the previous result and selection");
    check(mutations.length === 1 && mutations[0] === "/v1/duels/practice/answer", "Trying a question never creates, joins or stakes a duel");
    await context.close();
  }
  check(report.errors.length === 0, "No browser runtime errors");
  check(report.unexpectedRequests.length === 0, "All account and game requests stayed within the local fixture");
  report.passed = true;
} finally {
  writeFileSync(path.join(out, "member-games-report.json"), JSON.stringify(report, null, 2));
  await browser.close();
}
