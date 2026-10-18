/** Real, public-tour end-to-end checks. Runs a fresh temporary Edge context only.
 * node tools/tours/verify.mjs [http://localhost:3214] [output-directory] [flows]
 * Optional flows is a comma-separated subset: full,short,navigation,storage,mobile.
 * PLAYWRIGHT_MODULE may point at a bundled playwright package; EDGE_EXECUTABLE
 * may override the installed Edge binary. No account, practice API or user profile.
 */
import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import assert from "node:assert/strict";

const require = createRequire(import.meta.url);
const playwright = require(process.env.PLAYWRIGHT_MODULE || "C:/Users/harel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const { chromium } = playwright;
const base = (process.argv[2] || "http://localhost:3214").replace(/\/$/, "");
const out = path.resolve(process.argv[3] || path.join(process.cwd(), "../../.impeccable/review/muxi/e2e"));
const requestedFlows = process.argv[4]?.split(",").filter(Boolean);
const appRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")), "../..");
await fs.mkdir(out, { recursive: true });
const catalog = await fs.readFile(path.join(appRoot, "src/lib/muxi-tour.ts"), "utf8");
const fullIds = [...catalog.slice(catalog.indexOf("export const FULL_TOUR"), catalog.indexOf("const byId")).matchAll(/step\("([^"]+)"/g)].map(m => m[1]);
const shortIds = [...catalog.slice(catalog.indexOf("export const SHORT_TOUR"), catalog.indexOf("export const tourSteps")).matchAll(/byId\("([^"]+)"/g)].map(m => m[1]);
const report = { base, startedAt: new Date().toISOString(), fullCatalog: fullIds, shortCatalog: shortIds, checks: [], flows: [], consoleErrors: [], pageErrors: [], forbiddenRequests: [], screenshots: [] };
let current = "startup";
const check = (condition, message) => { assert.ok(condition, message); report.checks.push({ name: message, passed: true }); };
const edge = process.env.EDGE_EXECUTABLE || "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const browser = await chromium.launch({ executablePath: edge, headless: true });
let activePage;
const text = (he, en) => new RegExp(`${he}|${en}`);
const button = (p, he, en) => p.getByRole("button", { name: text(he, en), exact: true });
const stage = p => p.locator("[data-muxi-stage]");
const coach = p => p.locator("[data-muxi-coach]").first();
const next = p => coach(p).getByRole("button", { name: /^(ממשיכים|Continue|סיום הסיור|Finish tour)/ });
const root = p => p.locator("[data-muxi-station]");
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

async function context(options = {}, init) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true, reducedMotion: "reduce", ...options });
  if (init) await ctx.addInitScript(init);
  const p = await ctx.newPage(); activePage = p; p.setDefaultTimeout(9000);
  p.on("console", message => { if (message.type() === "error") report.consoleErrors.push({ flow: current, text: message.text(), location: message.location() }); });
  p.on("response", response => { if (response.status() >= 400) (report.httpErrors ??= []).push({ flow: current, status: response.status(), url: response.url() }); });
  p.on("pageerror", error => report.pageErrors.push({ flow: current, text: error.message }));
  p.on("request", request => {
    if (p.url().includes("/tour") && /\/v1\/|supabase\.co\/(?:storage|rest|functions)|api\.anthropic\.com|api\.openai\.com/.test(request.url())) report.forbiddenRequests.push({ flow: current, method: request.method(), url: request.url() });
  });
  await p.goto(`${base}/tour`, { waitUntil: "networkidle", timeout: 90000 });
  await p.getByRole("heading", { name: /נעים להכיר, אני מוקסי|Hi, I'm Muxi/ }).waitFor();
  return { ctx, p };
}
async function shot(p, name, locator) {
  const target = path.join(out, `${name.replace(/[<>:"/\\|?*\u0000-\u001f]/g, "-")}.png`);
  if (locator) await locator.screenshot({ path: target }); else await p.screenshot({ path: target, fullPage: false });
  report.screenshots.push(target);
}
async function captureFailure(p, error) {
  try {
    await shot(p, `failure-${current.replace(/[^a-z0-9-]/gi, "-")}`);
    (report.failureEvidence ??= []).push({ phase: current, error: error.message, station: await root(p).getAttribute("data-muxi-station"), visibleText: (await p.locator("body").innerText()).slice(-16000) });
  } catch {}
}
async function station(p, id) {
  await p.waitForFunction(value => document.querySelector("[data-muxi-station]")?.getAttribute("data-muxi-station") === value, id);
  await stage(p).locator("[data-muxi-target]").first().waitFor();
  check(await root(p).getAttribute("data-muxi-station") === id, `${current}: station ${id} rendered`);
}
async function continueStation(p) {
  await next(p).waitFor();
  await p.waitForFunction(() => { const buttons = [...document.querySelectorAll("[data-muxi-coach] button")]; return buttons.some(b => /^(ממשיכים|Continue|סיום הסיור|Finish tour)/.test(b.textContent ?? "") && !b.disabled); });
  await next(p).click();
}
async function language(p, lang) {
  await p.getByRole("button", { name: /שפה: עברית. החלפת שפה|Language: English. Change language/ }).click();
  await p.getByRole("menuitemradio", { name: lang === "en" ? "English" : "עברית", exact: true }).click();
  await p.waitForFunction(value => document.documentElement.lang === value, lang);
}
async function theme(p) { await p.getByRole("button", { name: /מעבר למצב כהה|מעבר למצב בהיר|Switch to dark mode|Switch to light mode/ }).click(); }
async function expandChapters(p, name) {
  await button(p, "כל הפרקים", "All chapters").click();
  await p.getByRole("navigation", { name: /פרקי הסיור|Tour chapters/ }).getByRole("button", { name }).click();
}
async function overflow(p, label) {
  const result = await p.evaluate(() => {
    const elements = [document.documentElement, document.querySelector("[data-muxi-station]"), document.querySelector("dialog:modal"), ...document.querySelectorAll("[data-muxi-coach]")].filter(Boolean);
    return elements.map(e => ({ tag: e.tagName, width: e.clientWidth, scroll: e.scrollWidth, overflow: e.scrollWidth > e.clientWidth + 2 }));
  });
  check(result.every(e => !e.overflow), `${label}: document and overlay widths contained (${JSON.stringify(result)})`);
}
async function codeExercise(p, completion = false) {
  const s = stage(p);
  await button(s, "העתקת קוד השאלה לעורך", "Copy question code into editor").click();
  const editor = s.getByRole("textbox", { name: /עורך קוד ותוכן טכני|Code and technical content editor/ });
  await editor.fill("int sum_samples(const int *a, size_t n) {\n  int total = 0;\n  for (size_t i = 0; i < n; ++i) total += a[i];\n  return total;\n}\n");
  check((await editor.textContent()).includes("i < n"), `${current}: actual code editor accepts a corrected C loop`);
  if (completion) {
    await editor.press("Control+End"); await editor.pressSequentially("pri", { delay: 40 }); await editor.press("Control+Space");
    await p.getByRole("listbox").waitFor();
    check(await p.getByRole("option", { name: /printf/ }).count() > 0, "C completion offers printf");
    await shot(p, "c-completion"); await editor.press("Escape"); await editor.press("Escape"); await editor.press("Tab");
    check(!(await editor.evaluate(e => e.contains(document.activeElement))), "Esc then Tab exits CodeMirror keyboard focus");
  }
}
async function ensureRunning(p) {
  await stage(p).locator(".simulation-bar").waitFor();
  const run = button(stage(p), "הרצת סימולציה", "Run simulation");
  if (await run.count()) await run.click();
}
async function selectPart(p, value) {
  await stage(p).getByLabel(/בחירת רכיב להגדרה|Select component to configure/).selectOption(value);
}
async function inputToggle(p) { await stage(p).getByRole("button", { name: /החלפת 0 \/ 1|Toggle 0 \/ 1/ }).click(); }
async function circuitSnapshot(dialog) {
  return {
    nodes: await dialog.locator(".react-flow__node").allTextContents(),
    edges: await dialog.locator(".react-flow__edge").count(),
    running: await dialog.getByRole("button", { name: /^(עצירת סימולציה|Stop simulation)$/ }).count(),
  };
}
async function guidancePreservesCircuit(p, dialog, mobile = false, suffix = "") {
  const panel = dialog.locator("[data-muxi-expanded-guide]");
  const snapshot = await circuitSnapshot(dialog);
  check(snapshot.running === 1, `${mobile ? "Mobile" : "Desktop"} expanded simulation remains running`);
  check(await panel.getByRole("button", { name: /^(יציאה מהסיור|Exit tour)$/ }).isVisible(), `${mobile ? "Mobile" : "Desktop"} expanded guidance always exposes exit`);
  if (mobile) {
    check(await panel.getAttribute("data-minimized") === "true", "Mobile guidance starts minimized");
    check(!(await panel.locator("[data-muxi-coach]").isVisible()), "Minimized mobile guidance hides its expanded body");
    const box = await panel.boundingBox();
    check(box.height < 180, "Minimized mobile guide leaves the drawing canvas usable");
    // Use actual drawing controls with the coach minimized, rather than just
    // asserting that the sheet is smaller than the viewport.
    await button(dialog, "עצירת סימולציה", "Stop simulation").click();
    check(await button(dialog, "הרצת סימולציה", "Run simulation").isVisible(), "Circuit simulation can be stopped while mobile guidance is minimized");
    await button(dialog, "הרצת סימולציה", "Run simulation").click();
    check(await button(dialog, "עצירת סימולציה", "Stop simulation").isVisible(), "Circuit simulation can be restarted while mobile guidance is minimized");
    await dialog.locator(".circuit-canvas").scrollIntoViewIfNeeded();
    await shot(p, `mobile-expanded-minimized${suffix}`);
    await button(panel, "פתיחת ההדרכה", "Open guidance").click();
  } else {
    check(await panel.getAttribute("data-minimized") === "false", "Desktop guidance starts expanded");
  }
  check(await panel.locator("[data-muxi-coach]").isVisible(), `${mobile ? "Mobile" : "Desktop"} expanded guidance is readable after opening`);
  await button(panel, "מזעור ההדרכה", "Minimize guidance").click();
  check(!(await panel.locator("[data-muxi-coach]").isVisible()), `${mobile ? "Mobile" : "Desktop"} guidance can be minimized manually`);
  check(await panel.getByRole("button", { name: /^(יציאה מהסיור|Exit tour)$/ }).isVisible(), "Exit remains accessible while guidance is minimized");
  await button(panel, "פתיחת ההדרכה", "Open guidance").focus();
  await p.keyboard.press("Tab");
  check(await p.evaluate(() => /^(יציאה מהסיור|Exit tour)$/.test(document.activeElement?.getAttribute("aria-label") ?? "")), `${mobile ? "Mobile" : "Desktop"} compact guide keyboard Tab reaches the exit`);
  await p.keyboard.press("Shift+Tab"); await p.keyboard.press("Enter");
  check(await panel.locator("[data-muxi-coach]").isVisible(), `${mobile ? "Mobile" : "Desktop"} guidance reopens with keyboard Enter`);
  check(JSON.stringify(await circuitSnapshot(dialog)) === JSON.stringify(snapshot), `${mobile ? "Mobile" : "Desktop"} minimizing and reopening preserve circuit nodes, wires, displayed signals and running simulation`);
}
async function perform(p, id, full = false) {
  const s = stage(p);
  switch (id) {
    case "goal":
      await s.getByLabel(/לאיזה כיוון מתכוננים|What are you preparing for/).selectOption("software");
      await s.getByLabel(/מועד ראיון משוער|Estimated interview date/).fill("2026-12-15");
      await s.getByLabel(/כמה דקות ביום|Minutes per day/).selectOption("25");
      await button(s, "שמירת יעד לדוגמה", "Save example goal").click(); break;
    case "search":
      for (const alias of ["Intel", "INTEL", "אינטל"]) {
        await s.getByRole("searchbox").fill(alias);
        check(await s.getByRole("button", { name: /דוגמת סינון|filter example/ }).count() === 4, `Company alias ${alias} returns the same four original examples`);
      } break;
    case "filter":
      await s.getByRole("searchbox").fill(""); await s.getByLabel(/סינון לפי נושא|Filter by topic/).selectOption("digital");
      check(await s.getByRole("button", { name: /דוגמת סינון|filter example/ }).count() === 1, "Topic filter narrows the library"); break;
    case "digital": case "fsm": case "programming": case "algorithms": case "reasoning-topic": case "behavioral": case "design-topic": case "communication": case "analog": {
      await s.getByRole("searchbox").fill(""); await s.getByLabel(/סינון לפי נושא|Filter by topic/).selectOption("all");
      const names = { digital: /החלטת רוב משלושה חיישנים|Three-sensor majority/, fsm: /גילוי הרצף 101|Detect the sequence 101/, programming: /איפה נגמר המערך|Where does the array end/, algorithms: /שתי רשימות ממוינות|Two sorted lists/, "reasoning-topic": /הקופסה עם התווית הלא נכונה|The mislabeled box/, behavioral: /החלטה ששיניתם בפרויקט|A project decision you changed/, "design-topic": /בחירה בין שני מקורות|Select between two sources/, communication: /שולח מהיר ומקבל עסוק|A fast sender and a busy receiver/, analog: /מחלק מתח עם עומס|A loaded voltage divider/ };
      await s.getByRole("button", { name: names[id] }).first().click();
      if (id === "communication") { await s.getByRole("button", { name: /מחלק מתח עם עומס|A loaded voltage divider/ }).first().click(); check(await s.getByText(/נושא עתידי:|Future topic:/).count() > 0, "Analog example is explicitly marked as a future topic"); }
      break;
    }
    case "explanation":
      await s.getByRole("textbox", { name: /הסבר הפתרון|Solution explanation/ }).fill("אבחר בקופסה המסומנת מעורב: התווית שגויה ולכן הפריט הראשון קובע מה יש בה.");
      await s.getByText(/איך פועלת הכתבה קולית|How does voice dictation work/).click(); break;
    case "code": await codeExercise(p, full); break;
    case "languages":
      await s.getByRole("combobox", { name: /שפת הקוד|Code language/ }).selectOption("python");
      check((await s.getByRole("textbox", { name: /עורך קוד ותוכן טכני|Code and technical content editor/ }).textContent()).includes("sum_samples"), "Changing code language preserves the code draft"); break;
    case "wire":
      await s.locator(".circuit-connect > summary").click();
      await s.locator(".circuit-connect").getByRole("combobox", { name: /^(יציאה|Output)/ }).selectOption("b:Q");
      await s.locator(".circuit-connect").getByRole("combobox", { name: /^(כניסה|Input)/ }).selectOption("and:A1");
      await button(s.locator(".circuit-connect"), "חיבור", "Connect").click(); break;
    case "simulate":
      if (!full) await button(s, "טעינת דוגמה מחוברת מראש במקום לחווט ידנית", "Load a prewired example instead of wiring manually").click();
      await ensureRunning(p); break;
    case "inputs": await selectPart(p, "a"); await inputToggle(p); break;
    case "truth":
      await button(s, "יצירת טבלת אמת", "Generate truth table").click();
      check(await s.getByRole("table").count() === 1, "Real truth table is generated");
      check(await s.getByRole("table").locator("tbody tr").count() === 4, "Two-input AND truth table has four rows");
      await shot(p, "full-circuit-truth-table"); break;
    case "palette": await s.locator(".component-palette").getByRole("button", { name: "NOT", exact: true }).click(); break;
    case "configure": await selectPart(p, "and"); await s.getByLabel(/שם הרכיב|Component label/).fill("AND checked"); break;
    case "undo": await s.getByRole("button", { name: /ביטול שינוי במעגל|Undo circuit change/ }).click(); break;
    case "expand": {
      await button(s, "הרחבת הלוח", "Expand drawing").click();
      const dialog = p.locator("dialog:modal"); await dialog.waitFor();
      check(await dialog.locator("[data-muxi-coach]").count() === 1, "Expanded native circuit dialog contains Muxi coach");
      await guidancePreservesCircuit(p, dialog);
      check(await dialog.getByRole("button", { name: /ממשיכים|Continue/ }).isEnabled(), "Expanded coach Continue remains usable");
      await overflow(p, "Desktop expanded circuit"); await shot(p, "expanded-circuit-coach");
      // Exercise the actual coach while the dialog is in the top layer.
      await dialog.getByRole("button", { name: /ממשיכים|Continue/ }).click();
      await station(p, "export-circuit");
      await button(p.locator("dialog:modal"), "חזרה לתשובה", "Back to answer").click();
      return "advanced";
    }
    case "export-circuit": {
      const downloaded = p.waitForEvent("download"); await s.getByRole("button", { name: /הורדת השרטוט|Download circuit/ }).click();
      const file = await downloaded; check(/\.json$/.test(file.suggestedFilename()), "Circuit export produces a portable JSON file"); break;
    }
    case "mux": await ensureRunning(p); await selectPart(p, "s"); await inputToggle(p); break;
    case "clock-start": await ensureRunning(p); break;
    case "clock": await ensureRunning(p); await s.getByRole("button", { name: /צעד שעון|Clock step/ }).click(); break;
    case "reset": await ensureRunning(p); await button(s, "איפוס", "Reset").click(); break;
    case "hint": await s.getByRole("button", { name: /פתיחת רמז 1 מתוך 3|Open hint 1 of 3/ }).click(); break;
    case "solution":
      await button(s, "צפייה בפתרון", "View solution").click();
      check(await button(s, "כן, הציגו את הפתרון", "Yes, reveal the solution").isVisible(), "Reference exposure requires explicit confirmation");
      await button(s, "אמשיך לנסות", "Keep trying").click();
      check(await next(p).isDisabled(), "Canceling reference exposure does not unlock the station");
      await button(s, "צפייה בפתרון", "View solution").click(); await button(s, "כן, הציגו את הפתרון", "Yes, reveal the solution").click(); break;
    case "materials": {
      await button(s, "פתיחת שרטוט השאלה", "Open question diagram").click();
      const downloaded = p.waitForEvent("download"); await button(s, "הורדת השאלה והפתרון לדוגמה", "Download example question and solution").click();
      check(/\.md$/.test((await downloaded).suggestedFilename()), "Question and solution resource download works"); break;
    }
    case "photo": {
      await button(s, "התנסות עם תמונת פתרון מקורית של מוקסי", "Try Muxi's original sample answer image").click();
      const preview = s.getByRole("img", { name: /תצוגה מקדימה מקומית|Local preview/ }); await preview.waitFor();
      check(await preview.evaluate(e => e.complete && e.naturalWidth > 0), "Original sample photo is decoded and previewed");
      await button(s, "הסרת התמונה", "Remove image").click();
      const filePath = path.join(out, "upload-fixture.png");
      // A browser-produced PNG is a valid local file, unlike hand-copied tiny
      // base64 fixtures whose decoder/CRC support varies between browsers.
      await p.screenshot({ path: filePath, clip: { x: 0, y: 0, width: 240, height: 120 } });
      await s.locator('input[type="file"]').setInputFiles(filePath); await preview.waitFor();
      check(await preview.evaluate(e => e.complete && e.naturalWidth > 0), "Actual local PNG file upload is processed and previewed");
      await s.locator('input[type="file"]').setInputFiles({ name: "invalid.txt", mimeType: "text/plain", buffer: Buffer.from("not an image") });
      await s.getByRole("alert").waitFor(); check(await preview.isVisible(), "Invalid file is rejected without discarding the valid preview"); break;
    }
    case "remove-photo": await button(s, "הסרת התמונה", "Remove image").click(); check(await s.getByRole("img").count() === 0, "Photo removal clears the preview"); break;
    case "feedback":
      await s.getByRole("textbox", { name: /הסבירו את הגישה שלכם|Explain your approach/ }).fill("אבדוק את שלושת הזוגות ואת כל שמונת צירופי הכניסות."); await button(s, "קבלת משוב לדוגמה", "Get example feedback").click();
      check(await s.getByText(/המשוב בסיור הוא דוגמה קבועה|Tour feedback is a fixed example/).count() > 0, "Feedback is honestly labeled fixed sample, not real AI assessment"); break;
    case "feedback-details": await s.getByText(/פתיחת הדגשים והצעד הבא לדוגמה|Open example focus areas and next step/).click(); break;
    case "followup": await s.getByRole("textbox", { name: /תשובה לשאלת ההמשך|Follow-up answer/ }).fill("כאשר C=1 נקבל Y=A+B ולכן חיישן נוסף יחיד כבר מספיק להכרעת רוב."); await button(s, "שמירת תשובת היכרות", "Save introduction answer").click(); break;
    case "reports":
      await s.getByLabel(/כמה בטוחים בפתרון|How confident are you/).selectOption("4"); await button(s, "שמירת הערכה עצמית לדוגמה", "Save example self-assessment").click();
      await s.getByRole("textbox", { name: /מה כדאי לתקן בשאלה|What should be corrected/ }).fill("כדאי להגדיר אם האיפוס סינכרוני או אסינכרוני."); await button(s, "שמירת דיווח מקומי לדוגמה", "Save a local example report").click(); break;
    case "interview": await s.getByLabel(/משך הראיון לדוגמה|Example interview duration/).selectOption("30"); await button(s, "התחלת ראיון היכרות", "Start introduction interview").click(); break;
    case "interview-answer": await s.getByRole("textbox", { name: /תשובת הראיון|Interview answer/ }).fill("העברה מתבצעת בקצה שעון כאשר valid וגם ready גבוהים. כאשר המקבל עסוק נשמור על הנתון."); await button(s, "שליחת התשובה לדוגמה", "Submit example answer").click(); break;
    case "interview-report": await button(s, "סיום ופתיחת דוח היכרות", "Finish and open introduction report").click(); check(await s.getByRole("heading", { name: /דוח ראיון היכרות|Introduction interview report/ }).count() > 0, "Local interview report opens with the submitted answer"); break;
    case "saved": await button(s, "שמירה לחזרה", "Bookmark for later").click(); break;
    case "history": await button(s, "פתיחת הניסיון", "Open attempt").click(); break;
    case "progress": await s.getByRole("button", { name: /מכונות מצבים — לחיזוק|FSMs — practice focus/ }).click(); break;
    case "readiness": await button(s, "פתיחת ראיות מוכנות לדוגמה", "Open example readiness evidence").click(); break;
    case "plan":
      const skill = s.getByRole("button", { name: /מכונות מצבים — לחיזוק|FSMs — practice focus/ });
      if (!(await button(s, "בחירת משימת ההמשך לדוגמה", "Choose the example next task").count())) await skill.click();
      await button(s, "בחירת משימת ההמשך לדוגמה", "Choose the example next task").click(); break;
    case "theme": await theme(p); check(await p.locator("html").getAttribute("data-theme") === "dark", `${current}: theme control applies dark mode`); await shot(p, `${current}-dark-settings`); break;
    case "language": await language(p, "en"); check(await stage(p).getByRole("heading", { name: "Make the site comfortable for you" }).isVisible(), "English translation updates in the active station"); await shot(p, "english-dark-settings"); break;
    default: throw new Error(`No actual interaction implemented for station ${id}`);
  }
}

async function fullTour() {
  const { ctx, p } = await context();
  try {
    await shot(p, "desktop-chooser"); await shot(p, "muxi-mascot", p.getByRole("img", { name: "מוקסי מנופף לשלום" }));
    await button(p, "מתחילים בסיור המעמיק", "Start the full tour").click();
    let alreadyAt = null;
    for (const id of fullIds) {
      current = `full:${id}`; await station(p, id);
      check(await next(p).isDisabled(), `Full ${id}: Continue is disabled before the required interaction`);
      const result = await perform(p, id, true);
      if (result === "advanced") { alreadyAt = "export-circuit"; continue; }
      await continueStation(p);
      if (id === "goal") {
        await station(p, "search"); await coach(p).getByRole("button", { name: "התחנה הקודמת", exact: true }).click(); await station(p, "goal");
        check(await next(p).isEnabled(), "Backtracking retains completed stations"); await continueStation(p);
      }
      alreadyAt = null;
    }
    await p.getByRole("heading", { name: /עכשיו הכלים בידיים שלכם|The tools are yours to use/ }).waitFor();
    const saved = await p.evaluate(() => JSON.parse(localStorage.getItem("jobrun-muxi-tour-v1-visitor") || "null"));
    check(saved.status === "completed" && saved.completed.length === fullIds.length && saved.skipped.length === 0, `Full tour completed all ${fullIds.length} stations with zero skips`);
    await shot(p, "full-completion");
  } catch (error) { await captureFailure(p, error); throw error; } finally { await ctx.close(); }
}
async function shortTour() {
  const { ctx, p } = await context();
  try {
    await button(p, "מתחילים בסיור הקצר", "Start the short tour").click();
    for (const id of shortIds) { current = `short:${id}`; await station(p, id); check(await next(p).isDisabled(), `Short ${id}: Continue gated before interaction`); await perform(p, id); await continueStation(p); }
    await p.getByRole("heading", { name: /עכשיו הכלים בידיים שלכם|The tools are yours to use/ }).waitFor();
    const saved = await p.evaluate(() => JSON.parse(localStorage.getItem("jobrun-muxi-tour-v1-visitor") || "null"));
    check(saved.completed.length === shortIds.length && saved.skipped.length === 0, `Short tour completed all ${shortIds.length} stations with zero skips`);
    await shot(p, "short-completion");
    await button(p, "ממשיכים לסיור המעמיק", "Explore the full tour").click(); await station(p, "goal"); check(await next(p).isDisabled(), "Short completion can launch a fresh full tour");
  } catch (error) { await captureFailure(p, error); throw error; } finally { await ctx.close(); }
}
async function navigationAndPersistence() {
  const { ctx, p } = await context();
  try {
    await button(p, "מתחילים בסיור המעמיק", "Start the full tour").click(); await station(p, "goal");
    const focused = await p.evaluate(() => document.activeElement?.tagName); check(focused === "H2", "Tour start focuses the coach heading");
    await p.keyboard.press("Tab"); check(await p.evaluate(() => document.activeElement?.tagName === "BUTTON"), "Keyboard Tab reaches a usable tour control");
    await perform(p, "goal"); await continueStation(p); await station(p, "search");
    await coach(p).getByRole("button", { name: "יציאה ושמירת המקום", exact: true }).click(); await p.waitForURL(`${base}/`, { waitUntil: "domcontentloaded" });
    await p.goto(`${base}/tour`, { waitUntil: "networkidle" }); await button(p, "ממשיכים מהמקום שעצרנו", "Resume where I stopped").click(); await station(p, "search");
    check(await next(p).isDisabled(), "Pause/resume restores the station while preserving action gate");
    await expandChapters(p, "בונים ובודקים מעגל"); await station(p, "wire");
    await coach(p).getByRole("button", { name: "בחירת סיור אחר", exact: true }).click();
    await button(p, "מתחילים בסיור הקצר", "Start the short tour").click(); await station(p, "goal");
    check(await next(p).isDisabled(), "Choosing another tour starts its own progress");
    await coach(p).getByRole("button", { name: "דלגו על התחנה הזאת", exact: true }).click(); await station(p, "search");
    const saved = await p.evaluate(() => JSON.parse(localStorage.getItem("jobrun-muxi-tour-v1-visitor") || "null")); check(saved.skipped.includes("goal") && !saved.completed.includes("goal"), "Skip is tracked separately from completion");
    await p.keyboard.press("Escape"); await p.waitForURL(`${base}/`, { waitUntil: "domcontentloaded" }); check(true, "Escape exits a tour with no native dialog open");
  } catch (error) { await captureFailure(p, error); throw error; } finally { await ctx.close(); }
}
async function storageRobustness() {
  for (const kind of ["corrupt", "blocked"]) {
    current = `storage:${kind}`;
    const { ctx, p } = await context({}, kind === "corrupt" ? () => { localStorage.setItem("jobrun-muxi-tour-v1-visitor", "{broken json"); } : () => { Object.defineProperty(Storage.prototype, "getItem", { value() { throw new DOMException("Blocked for storage test", "SecurityError"); } }); Object.defineProperty(Storage.prototype, "setItem", { value() { throw new DOMException("Blocked for storage test", "SecurityError"); } }); });
    try { await button(p, "מתחילים בסיורהקצר", "Start the short tour").or(button(p, "מתחילים בסיור הקצר", "Start the short tour")).click(); await station(p, "goal"); await perform(p, "goal"); await continueStation(p); await station(p, "search"); check(true, `${kind} localStorage does not prevent starting and using the tour`); }
    catch (error) { await captureFailure(p, error); throw error; } finally { await ctx.close(); }
  }
}
async function mobile() {
  const { ctx, p } = await context({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  try {
    await overflow(p, "Mobile chooser Hebrew"); await shot(p, "mobile-chooser-light");
    await language(p, "en"); await theme(p); await overflow(p, "Mobile chooser English dark"); await shot(p, "mobile-chooser-dark-english"); await language(p, "he");
    await button(p, "מתחילים בסיור המעמיק", "Start the full tour").click(); await station(p, "goal");
    await p.waitForFunction(() => document.querySelector("[data-muxi-coach] svg[data-point-direction]")?.getAttribute("data-point-direction") === "down");
    check(await coach(p).locator("svg[data-point-direction]").getAttribute("data-point-direction") === "down", "Mobile Muxi points down toward the exercise");
    await overflow(p, "Mobile goal"); await shot(p, "mobile-exercise-goal");
    await expandChapters(p, "בונים ובודקים מעגל"); await station(p, "wire"); await perform(p, "wire", true); await continueStation(p); await station(p, "simulate"); await ensureRunning(p);
    await overflow(p, "Mobile circuit"); await shot(p, "mobile-circuit-dark");
    await button(stage(p), "הרחבת הלוח", "Expand drawing").click(); await p.locator("dialog:modal").waitFor();
    await guidancePreservesCircuit(p, p.locator("dialog:modal"), true);
    await overflow(p, "Mobile expanded circuit and coach"); await shot(p, "mobile-expanded-coach");
    await button(p.locator("dialog:modal"), "חזרה לתשובה", "Back to answer").click();
    await p.getByRole("button", { name: /מעבר למצב בהיר/ }).click(); await overflow(p, "Mobile circuit light");
    await language(p, "en");
    await button(stage(p), "הרחבת הלוח", "Expand drawing").click(); await p.locator("dialog:modal").waitFor();
    await guidancePreservesCircuit(p, p.locator("dialog:modal"), true, "-en");
    await overflow(p, "Mobile expanded circuit English light"); await shot(p, "mobile-expanded-coach-en");
    const compact = p.locator("dialog:modal [data-muxi-expanded-guide]");
    if (await compact.getAttribute("data-minimized") !== "true") await button(compact, "מזעור ההדרכה", "Minimize guidance").click();
    await compact.getByRole("button", { name: /^(יציאה מהסיור|Exit tour)$/, exact: true }).click(); await p.waitForURL(`${base}/`, { waitUntil: "domcontentloaded" });
    check(true, "Always-visible compact guidance exit leaves the native drawing dialog and tour");
  } catch (error) { await captureFailure(p, error); throw error; } finally { await ctx.close(); }
}
try {
  for (let i = 0; i < 30; i++) { try { if ((await fetch(`${base}/tour`)).ok) break; } catch {} await wait(1000); }
  for (const [name, fn] of [["full", fullTour], ["short", shortTour], ["navigation", navigationAndPersistence], ["storage", storageRobustness], ["mobile", mobile]].filter(([name]) => !requestedFlows || requestedFlows.includes(name))) {
    current = name;
    try { await fn(); report.flows.push({ name, passed: true }); console.log(`PASS ${name}`); }
    catch (error) {
      const failure = { name, phase: current, passed: false, error: error.stack || String(error) };
      if (activePage && !activePage.isClosed()) { try { failure.station = await root(activePage).getAttribute("data-muxi-station"); await shot(activePage, `failure-${name}`); failure.visibleText = (await activePage.locator("body").innerText()).slice(-10000); } catch {} }
      report.flows.push(failure); console.error(`FAIL ${name} at ${current}: ${error.message}`);
    }
  }
  check(report.forbiddenRequests.length === 0, "Public tours made no practice, storage or AI-provider requests");
  check(report.pageErrors.length === 0, "No uncaught browser errors");
  check(report.consoleErrors.length === 0, "No browser console errors");
} catch (error) { report.finalError = error.stack || String(error); }
finally {
  await browser.close(); report.finishedAt = new Date().toISOString();
  report.passed = report.flows.length === (requestedFlows?.length || 5) && report.flows.every(f => f.passed) && !report.finalError;
  await fs.writeFile(path.join(out, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ passed: report.passed, checks: report.checks.length, flows: report.flows.map(({ name, passed, phase }) => ({ name, passed, phase })), report: path.join(out, "report.json") }, null, 2));
  process.exitCode = report.passed ? 0 : 1;
}
