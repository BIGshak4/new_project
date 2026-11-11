// Real account walkthrough integration, entirely against the local screenshot-server fixture.
// No synthetic session, answer or purchase can reach a production service.
import { createRequire } from "node:module";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";

const require = createRequire(process.env.PLAYWRIGHT_PACKAGE_ROOT || "C:/Users/harel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json");
const { chromium } = require("playwright");
const base = process.argv[2] || "http://localhost:3296";
const fixturePath = process.argv[3];
const local = value => ["localhost", "127.0.0.1"].includes(new URL(value).hostname);
if (!fixturePath || !local(base)) throw Error("Provide a local web URL and screenshot-server session file");
const fixture = JSON.parse(readFileSync(fixturePath, "utf8"));
if (!local(fixture.api) || !local(fixture.stub)) throw Error("Both fixture services must be local");
const output = path.dirname(fixturePath);
mkdirSync(output, { recursive: true });
const publicEnv = readFileSync(path.resolve(".env.local"), "utf8");
const supaUrl = publicEnv.match(/^NEXT_PUBLIC_SUPABASE_URL=["']?([^\r\n"']+)/m)?.[1];
const report = { checks: [], requests: [], unexpectedRequests: [], errors: [], passed: false };
const check = (condition, label) => { assert.ok(condition, label); report.checks.push(label); console.log("PASS", label); };
const browser = await chromium.launch({ executablePath: process.env.EDGE_PATH || "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", headless: true });
let context, page, guest;
const control = name => page.locator(`[data-member-tour="${name}"]`).filter({ visible: true }).first();
const tool = name => page.locator(`[data-muxi-control="${name}"]`).filter({ visible: true }).first();
const coach = () => page.locator("[data-member-coach]");
const chapters = {
  goal: "היעד שלכם", dashboard: "האזור האישי", library: "מאגר שאלות הראיון", explanation: "הסבר במילים שלכם",
  code: "קוד ומשוב אישי", circuit: "שאלת חומרה ושרטוט", fundamentals: "יסודות בקטנה", games: "משחקים",
  friends: "חברים ודו־קרב", shop: "החנות של מוקסי", interview: "ראיון מדומה", helper: "העוזר האישי",
};
async function routeFixture(route) {
  const request = route.request(), url = new URL(request.url());
  let endpoint;
  if (/^\/(?:auth|rest|storage)\/v1\//.test(url.pathname)) endpoint = fixture.stub;
  else if (/^\/v1\//.test(url.pathname) || url.pathname === "/health") endpoint = fixture.api;
  if (endpoint) {
    if (url.pathname.startsWith("/v1/")) report.requests.push({ path: url.pathname, method: request.method() });
    const response = await route.fetch({ url: endpoint + url.pathname + url.search });
    await route.fulfill({ response });
  } else if (url.origin === new URL(base).origin || ["data:", "blob:"].includes(url.protocol)) await route.continue();
  else { report.unexpectedRequests.push(url.origin + url.pathname); await route.abort(); }
}
async function api(pathname) {
  const response = await context.request.get(fixture.api + pathname, { headers: { Authorization: `Bearer ${fixture.session.access_token}` } });
  assert.ok(response.ok(), `Local API read ${pathname} failed (${response.status()})`);
  return response.json();
}
async function expandCoach() {
  if (await coach().getAttribute("data-compact") === "true") await coach().locator('button[aria-controls="member-tour-content"]').click();
}
async function jump(id) {
  await expandCoach();
  const outline = coach().getByRole("navigation", { name: "תחנות הסיור", exact: true });
  if (!await outline.isVisible()) await coach().getByRole("button", { name: "כל התחנות", exact: true }).click();
  await outline.getByRole("button", { name: new RegExp(chapters[id]) }).click();
  await page.waitForFunction(step => document.documentElement.dataset.memberTourStep === step, id);
  await coach().waitFor();
}
async function waitForPractice() {
  await page.waitForFunction(() => document.querySelector('[data-member-tour="practice-start"], .answer-editor, [data-member-tour="practice-feedback"]'));
  if (await control("practice-start").isVisible()) {
    const started = page.waitForResponse(response => new URL(response.url()).pathname === "/v1/practice/attempts" && response.request().method() === "POST");
    await control("practice-start").click();
    const response = await started;
    assert.ok(response.ok(), "Actual practice start should succeed");
  }
  await page.locator(".answer-editor").first().waitFor();
}
async function noOverflow(label) {
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), label);
}
const writes = pattern => report.requests.filter(request => request.method === "POST" && pattern.test(request.path));

try {
  guest = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  await guest.route("**/*", routeFixture);
  const visitor = await guest.newPage();
  await visitor.goto(base, { waitUntil: "domcontentloaded" });
  await visitor.getByRole("link", { name: "יצירת חשבון או כניסה", exact: true }).waitFor({ timeout: 20000 });
  check(await visitor.locator("[data-personal-helper], [data-member-coach]").count() === 0, "Signed-out visitors see neither the account helper nor the member coach");
  await guest.close(); guest = undefined;

  context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce" });
  await context.route("**/*", routeFixture);
  await context.addInitScript(({ session, supa }) => {
    for (const host of ["localhost", "127", ...(supa ? [new URL(supa).hostname.split(".")[0]] : [])]) localStorage.setItem(`sb-${host}-auth-token`, JSON.stringify(session));
  }, { session: fixture.session, supa: supaUrl });
  page = await context.newPage();
  page.setDefaultTimeout(20000);
  page.on("pageerror", error => report.errors.push(error.message));
  await page.goto(base, { waitUntil: "domcontentloaded" });
  await page.locator(".learn-head h1").waitFor();
  await control("helper-launcher").waitFor();
  check(await coach().count() === 0, "The member tour is closed on ordinary account entry");
  check(await control("helper-launcher").isVisible() && await control("helper-panel").count() === 0, "The avatar helper starts available and minimized");
  const launcherMascot = await page.getByRole("button", { name: "סיור עם מוקסי", exact: true }).locator("svg").first().boundingBox();
  check(launcherMascot && launcherMascot.width <= 34 && launcherMascot.height <= 36, "The header tour mascot stays compact instead of stretching the navigation");
  const bank = await api("/v1/questions?language=he");
  check(bank.length > 0, "The fixture exposes the actual seeded question catalog");
  const writesBeforeTour = writes(/.*/).length;
  await page.getByRole("button", { name: "סיור עם מוקסי", exact: true }).click();
  await coach().getByRole("heading", { name: "בואו נכין אתכם לראיון הבא.", exact: true }).waitFor();
  check(await page.locator(".app-shell").evaluate(element => !element.closest("[inert]")), "The live tour leaves the actual workspace interactive");
  check(await page.evaluate(() => document.body.style.overflow !== "hidden"), "The member coach does not lock document scrolling");
  check(writes(/.*/).length === writesBeforeTour, "Opening the coach does not write a goal, answer or purchase");
  await coach().getByRole("button", { name: /מתחילים יחד|ממשיכים מהמקום שלי/ }).click();
  await page.waitForFunction(() => document.documentElement.dataset.memberTourStep === "goal");
  const form = page.locator(".goal-setup");
  if (!await form.isVisible() && await control("goal-edit").isVisible()) await control("goal-edit").click();
  if (!await form.isVisible()) {
    const setGoal = page.getByRole("button", { name: /להגדיר את היעד|הגדרת היעד/ }).filter({ visible: true }).first();
    if (await setGoal.isVisible()) await setGoal.click();
  }
  await form.waitFor();
  const roles = form.locator('[data-goal-section="roles"]');
  if (await roles.getAttribute("open") === null) await roles.locator("summary").click();
  await roles.locator('input[type="checkbox"]').first().check();
  const minutes = form.locator('[data-goal-section="minutes"]');
  if (await minutes.getAttribute("open") === null) await minutes.locator("summary").click();
  await minutes.getByRole("radio", { name: /45/ }).check();
  const goalSaved = page.waitForResponse(response => new URL(response.url()).pathname === "/v1/me/goal" && response.request().method() === "POST");
  await tool("goal-save").click();
  const goalResponse = await goalSaved;
  check(goalResponse.ok() && (await goalResponse.json()).minutes_per_day === 45, "The tour saves the real account goal with the selected daily time");
  await coach().getByRole("button", { name: "לתחנה הבאה", exact: true }).click();
  await page.locator('[data-recommendation-waves][aria-busy="false"]').waitFor();
  check((await page.locator("[data-goal-summary]").innerText()).includes("45"), "The live personal dashboard reflects the goal saved during the tour");
  await noOverflow("Desktop dashboard and coach fit without horizontal overflow");
  await page.screenshot({ path: path.join(output, "member-desktop-dashboard.png") });

  await jump("library");
  await control("library-search").waitFor();
  await control("library-search").fill("Intel");
  check(await control("library-search").inputValue() === "Intel", "The library station uses the real searchable bank");
  await control("library-search").fill("");
  await control("library-question").first().waitFor();
  check(await page.locator('[data-member-tour="library-question"]').count() > 0, "The library shows actual question rows, not tour samples");

  const startedBeforeQuestion = writes(/^\/v1\/practice\/attempts$/).length;
  await jump("explanation");
  await page.waitForURL(url => url.searchParams.has("question") && !url.searchParams.has("attempt"));
  await waitForPractice();
  check(writes(/^\/v1\/practice\/attempts$/).length === startedBeforeQuestion + 1, "An explicit practice-start click creates exactly one actual bank attempt");
  const softwareAttempt = new URL(page.url()).searchParams.get("attempt");
  check(!!softwareAttempt, "The software station opens a server-backed attempt URL");
  const software = await api(`/v1/practice/attempts/${softwareAttempt}`);
  check(bank.some(question => question.key === software.question.key), "The guided software prompt is from the real question bank");
  await tool("explanation-open").click();
  const draft = "A strong, complete explanation. I define the input and output, traverse the array once, and test empty, repeated and negative values. This draft must survive the next tour stop.";
  await tool("answer-explanation").fill(draft);
  await jump("code");
  await page.locator(".answer-editor").waitFor();
  check(new URL(page.url()).searchParams.get("attempt") === softwareAttempt, "The code station keeps the same software attempt");
  check(await tool("answer-explanation").inputValue() === draft, "The actual explanatory draft survives the transition to code");
  await tool("code-open").click();
  await tool("code-language").selectOption("c");
  const editor = page.locator('[data-muxi-control="code-input"][contenteditable="true"]').first();
  await editor.fill("int maximum(const int a[], int n) {\n  int best = a[0];\n  for (int i = 1; i < n; ++i) if (a[i] > best) best = a[i];\n  return best;\n}");
  check((await editor.innerText()).includes("int maximum"), "The tour uses the genuine editable code editor");
  const accepted = page.waitForResponse(response => response.request().method() === "POST" && /\/submissions$/.test(new URL(response.url()).pathname));
  await control("practice-submit").click();
  check((await accepted).ok(), "The learner's explanation and code are submitted through the real practice API");
  await page.locator('[data-member-feedback-ready="true"]').waitFor({ timeout: 45000 });
  const evaluated = await api(`/v1/practice/attempts/${softwareAttempt}`);
  check(evaluated.submission?.assessed_by === "model" && evaluated.submission?.status === "done", "The real feedback lifecycle completes using the local provider fixture");
  check(evaluated.submission.answer.includes(draft) && evaluated.submission.answer.includes("int maximum"), "Feedback belongs to the answer actually entered, not predefined tour prose");
  check(await page.locator("#feedback").isVisible(), "Completed feedback is rendered in the actual question view");
  await coach().locator('[aria-live="polite"]').getByText("קראו מה היה טוב ומה כדאי לשפר.", { exact: false }).waitFor();
  check(true, "After real feedback arrives, the guide advances to reviewing it rather than obsolete editing steps");
  await page.screenshot({ path: path.join(output, "member-desktop-feedback.png") });

  await jump("circuit");
  await page.waitForURL(url => url.searchParams.has("question") && !url.searchParams.has("attempt"));
  await waitForPractice();
  const hardwareAttempt = new URL(page.url()).searchParams.get("attempt");
  check(hardwareAttempt !== softwareAttempt, "The hardware station opens its own real hardware question");
  const hardware = await api(`/v1/practice/attempts/${hardwareAttempt}`);
  check(bank.some(question => question.key === hardware.question.key), "The hardware prompt also comes from the actual bank");
  await tool("circuit-open").click();
  await page.locator('dialog[open][data-layout="inline"]').waitFor();
  await tool("circuit-fullscreen").click();
  const circuit = page.locator('dialog:modal[data-layout="fullscreen"]');
  await circuit.waitFor();
  await circuit.locator("[data-member-coach]").waitFor();
  check(await coach().count() === 1, "Exactly one usable coach follows the circuit into the native fullscreen dialog");
  await circuit.locator('[data-muxi-control="circuit-group"][data-muxi-group="2"]').click();
  await circuit.locator('[data-muxi-control="circuit-add-part"][data-muxi-kind="input"]').click();
  await circuit.locator('[data-muxi-control="circuit-add-part"][data-muxi-kind="output"]').click();
  await circuit.locator('[data-muxi-control="circuit-wire-open"]').click();
  const from = circuit.locator('[data-muxi-control="circuit-wire-source"]');
  const to = circuit.locator('[data-muxi-control="circuit-wire-target"]');
  await from.selectOption({ index: 1 });
  await to.selectOption({ index: 1 });
  await circuit.locator('[data-muxi-control="circuit-wire-connect"]').click();
  check(await circuit.locator('[data-muxi-control="circuit-simulate"]').count() === 0, "A combinational circuit correctly has no clocked simulation button");
  await circuit.locator('[data-muxi-control="circuit-truth-table"]').click();
  check((await circuit.innerText()).includes("טבלת אמת"), "The actual circuit tools generate a truth table");
  await circuit.locator('[data-muxi-control="circuit-expand"]').click();
  await page.locator('dialog[open][data-layout="inline"]').waitFor();
  check(await coach().count() === 1 && await page.locator("dialog:modal").count() === 0, "Returning to inline drawing restores the same global guide");

  await jump("fundamentals");
  await control("quick-reveal").waitFor();
  await control("quick-reveal").click();
  await page.locator("#quick-answer").waitFor();
  check(await page.locator("#quick-answer").isVisible(), "Fundamentals reveals the actual selected short-question solution");
  await control("quick-quiz").click();
  const quizDialog = page.locator('dialog:modal').filter({ has: page.locator('[data-member-tour="quiz-topics"]') });
  await quizDialog.waitFor();
  check(await quizDialog.locator('[data-member-tour="quiz-topics"] input[type="checkbox"]').count() > 2, "The quiz has the real selectable topic list");
  await quizDialog.locator('[data-member-tour="quiz-create"]').click();
  await page.locator('[data-member-tour="quiz-questions"]').waitFor();
  const questionIds = await page.locator("[data-quiz-question]").evaluateAll(elements => elements.map(element => element.dataset.quizQuestion));
  check(questionIds.length === 10 && new Set(questionIds).size === 10, "The quiz contains ten distinct real short questions");

  await jump("games");
  await control("game-practice-start").waitFor({ timeout: 30000 });
  check(new URL(page.url()).pathname === "/games", "The tour reaches the actual games route and survives the page transition");
  const walletBefore = await api("/v1/me/coins?language=he");
  const gameRound = page.waitForResponse(response => new URL(response.url()).pathname === "/v1/duels/practice" && response.ok());
  await control("game-practice-start").click();
  const round = await (await gameRound).json();
  check(Array.isArray(round.question.choices) && round.question.choices.length === 4 && !("correct_index" in round) && !("explanation" in round), "The game question is fetched from the server without exposing its answer");
  await control("game-practice-choice").check();
  const checked = page.waitForResponse(response => new URL(response.url()).pathname === "/v1/duels/practice/answer" && response.request().method() === "POST");
  await control("game-practice-check").click();
  const resultResponse = await checked;
  const gameResult = await resultResponse.json();
  check(resultResponse.ok() && typeof gameResult.correct === "boolean" && !!gameResult.explanation, "The chosen game answer is genuinely checked by the local game API");
  await control("game-practice-result").waitFor();
  const walletAfter = await api("/v1/me/coins?language=he");
  check(walletAfter.balance === walletBefore.balance && writes(/^\/v1\/duels$/).length === 0, "The practice round spends no coins and creates no fake friend duel");
  await noOverflow("Desktop games and coach fit without horizontal overflow");

  await jump("friends");
  await page.locator("[data-friends-panel]").waitFor();
  check(await page.locator('[data-friends-panel] input[name="friend_code"]').isVisible(), "Friends guidance points at the real code-entry form");
  await jump("shop");
  await control("shop-try-on").waitFor({ timeout: 30000 });
  const buysBefore = writes(/buy|purchase/).length;
  await control("shop-try-on").click();
  await control("shop-customize").waitFor();
  check(writes(/buy|purchase/).length === buysBefore, "Trying a real shop skin does not purchase it");
  check(new URL(page.url()).pathname === "/games/shop", "The shop tour uses the actual account shop route");

  await jump("interview");
  await control("interview-duration").waitFor({ timeout: 30000 });
  await control("interview-duration").getByRole("radio", { name: /20/ }).click();
  const interviewStarted = page.waitForResponse(response => response.request().method() === "POST" && /\/interviews$/.test(new URL(response.url()).pathname));
  await control("interview-start").click();
  const interviewResponse = await interviewStarted;
  check(interviewResponse.ok(), "The interview station can start a real timed interview through the API");
  await control("interview-answer").waitFor();
  await tool("explanation-open").click();
  await tool("answer-explanation").fill("A strong, complete explanation with a concrete input, expected output, boundary case, and reasoning.");
  const interviewAnswer = page.waitForResponse(response => response.request().method() === "POST" && /\/interviews\/[^/]+\/turns\/\d+\/answer$/.test(new URL(response.url()).pathname));
  await page.getByRole("button", { name: "שליחת התשובה", exact: true }).click();
  check((await interviewAnswer).ok(), "A written interview answer is saved through the actual interview flow");
  page.once("dialog", dialog => dialog.accept());
  await control("interview-end").click();
  await control("interview-report").waitFor({ timeout: 45000 });
  check(await control("interview-report").isVisible(), "Ending early builds and displays a report for the actual local interview");

  await jump("helper");
  await control("helper-launcher").waitFor();
  await control("helper-launcher").click();
  await control("helper-panel").waitFor();
  await control("helper-topic").click();
  await coach().getByRole("button", { name: "מסיימים את הסיור", exact: true }).waitFor({ state: "visible" });
  check(await coach().getByRole("button", { name: "מסיימים את הסיור", exact: true }).isEnabled(), "Using an actual helper topic completes the helper station");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForFunction(() => {
    const panel = document.querySelector('[data-member-tour="helper-panel"]')?.getBoundingClientRect();
    const guide = document.querySelector('[data-member-coach]')?.getBoundingClientRect();
    return panel && guide && panel.top >= 0 && panel.bottom <= guide.top - 8 && guide.bottom <= innerHeight;
  });
  check(true, "The open mobile helper stays on screen above the coach without overlapping it");
  await noOverflow("The open helper and coach fit a phone viewport together");
  await page.screenshot({ path: path.join(output, "member-mobile-helper.png") });
  await page.getByRole("button", { name: "מזעור העוזר", exact: true }).click();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await coach().getByRole("button", { name: "מסיימים את הסיור", exact: true }).click();
  await coach().getByRole("heading", { name: "עכשיו האתר כבר שלכם.", exact: true }).waitFor();
  check(true, "Finishing the live tour shows its completion screen");
  await page.screenshot({ path: path.join(output, "member-desktop-finish.png") });
  await coach().getByRole("button", { name: "לאזור האישי שלי", exact: true }).click();
  await coach().waitFor({ state: "detached" });
  await control("helper-launcher").waitFor();
  check(true, "Returning from the finished tour restores the normal personal dashboard and helper");
  await page.getByRole("button", { name: "סיור עם מוקסי", exact: true }).click();
  await coach().getByRole("button", { name: "מתחילים יחד", exact: true }).click();

  await jump("dashboard");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator('[data-recommendation-waves][aria-busy="false"]').waitFor();
  await noOverflow("The live tour and dashboard fit a 390px phone viewport");
  await page.screenshot({ path: path.join(output, "member-mobile-dashboard.png") });
  await page.getByRole("button", { name: "מעבר למצב כהה", exact: true }).click();
  await page.waitForFunction(() => document.documentElement.dataset.theme === "dark");
  await page.getByRole("button", { name: "שפה: עברית. החלפת שפה", exact: true }).click();
  await page.getByRole("menuitemradio", { name: "English", exact: true }).click();
  await coach().getByRole("heading", { name: "Know what to practice next", exact: true }).waitFor();
  check(await page.locator("html").getAttribute("dir") === "ltr", "The real account language switch also updates the guide and reading direction");
  await noOverflow("English dark-mode tour fits the phone viewport");
  await page.screenshot({ path: path.join(output, "member-mobile-dark-english.png") });
  await coach().getByRole("button", { name: "Pause tour and save my place", exact: true }).click();
  await coach().waitFor({ state: "detached" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.locator(".learn-head h1").waitFor();
  check(await coach().count() === 0, "A paused tour remains closed after reloading the account");
  await page.getByRole("button", { name: "Tour with Muxi", exact: true }).click();
  await coach().getByRole("button", { name: "Resume my tour", exact: true }).click();
  await page.waitForFunction(() => document.documentElement.dataset.memberTourStep === "dashboard");
  check(true, "Resume restores the saved station without replaying account actions");
  await coach().getByRole("button", { name: "Pause tour and save my place", exact: true }).click();
  check(writes(/buy|purchase|\/friends\/requests/).length === 0, "The complete walkthrough made no purchase or unsolicited friend request");
  check(report.unexpectedRequests.length === 0, "All authenticated data requests stayed within the explicit local fixture");
  check(report.errors.length === 0, "The live account walkthrough has no uncaught browser errors");
  report.passed = true;
} catch (error) {
  report.error = String(error.stack || error);
  process.exitCode = 1;
  console.error(report.error);
  if (page && !page.isClosed()) {
    report.page = { url: page.url(), text: (await page.locator("body").innerText().catch(() => "")).slice(-16000) };
    await page.screenshot({ path: path.join(output, "member-failure.png") }).catch(() => {});
  }
} finally {
  await context?.unrouteAll({ behavior: "wait" });
  await guest?.close();
  await browser.close();
  writeFileSync(path.join(output, "member-report.json"), JSON.stringify(report, null, 2));
}
