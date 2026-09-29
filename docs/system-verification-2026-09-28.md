# System verification after the look-and-feel night — 28 September 2026

Written for Shaked and Harel. This is the second half of the night run that began on 25 September. The first half
(speed, many users, the code and profiling review) is in `docs/performance-2026-09-26.md`. This half is the look:
the design brief, the tokens, the landing page, the copy pass, and the screenshot harness that photographs every
signed-in screen. Afterwards the whole system was verified again. `backend/STATUS.md` §5o has the build notes.

## 1. How the night went

- **The agent workflows kept stalling.** The stage was planned as a fan-out of design agents. Their connections
  dropped repeatedly and the last workflow never left its first phase in twelve hours, so the work was done directly
  in the main session instead. The Fable usage limit was reached more than once; as Shaked asked, work continued on
  Opus 5.5 when that happened and came back to Fable when it was available.
- **The live suite fought the laptop, not the database.** Two live runs were accidentally started at the same
  time; the Session pooler refuses the project's tenth connection, so both errored. Every rerun after that lost its
  connection in the middle of a query ("connection was closed in the middle of operation", then "can't reconnect
  until the invalid savepoint is rolled back" for the rest of the batch), while Render's own round trip to the same
  database stayed at 3.7 ms and eight probes from this machine all connected within 1.5 s. The Windows event log
  gave the reason: the laptop entered Modern Standby at 20:42, two minutes into a run, and woke at 00:21; pytest
  reported the runs as taking 3 to 10 hours because they slept with the machine. A suite that talks to a remote
  database cannot survive that. The per-test timeout plugin (`pytest-timeout`, 180 s) was added so a stalled test
  fails instead of hanging. The last attempt was made with the machine awake; §3 has that result. The two
  real-model end-to-end scripts, which use the same database, passed earlier in the night, before the standby.
- **Two design skills were installed** under `.claude/skills/` for this and future sessions: Anthropic's
  `frontend-design` (the "what makes a page look generated" checklist) and Vercel's `web-interface-guidelines`
  (accessibility, forms, motion, right-to-left), the second with JobRun's own overrides. Both are vendored with
  their licences.
- **A design brief was written first** (`docs/design-brief-2026-09-27.md`) and every visual change was checked
  against it: our own palette (not Duolingo's), Nunito with Assistant for Hebrew, 18/24/28 px radii, the 3D
  button, soft shadows that take the colour of what casts them, one accent per meaning (orange streak, purple XP,
  yellow interview), no all-caps labels, no decorative numbering, true facts only on the landing page.

## 2. What was built

1. **The landing page.** Signing in used to be a bare form. It is now a page built around the most characteristic
   thing in the product: a real interview question (the two-out-of-three sensor vote), its answer, the grade,
   "+18 XP" and the follow-up, then six true facts (30 questions, 6 subjects, 6 job types, about 8 seconds to a
   grade, Hebrew and English, 20/30/45-minute interviews), the three daily steps drawn as path nodes, and the
   sign-in card. Hebrew and English, phone and desktop. The tasks app keeps its own screen.
2. **The token pass.** Fourteen all-caps or tracked-out rules removed; the pilot line is a quiet margin note instead
   of a yellow box on every screen; the button lifts on hover and presses down on click; question rows bounce on
   hover; cards carry one soft shadow; XP is purple everywhere.
3. **Copy in the coach's voice.** Headings say what the page is ("The question bank", "Where you stand", "Your
   practice", "Saved questions", "Mock interview", "Interview report") instead of placeholder sentences ("Let's
   think it through.", "See how far you've come.", "The interview is over."). The saved-answer card says what waits
   below it. The interview report says "not enough evidence yet" instead of a dash.
4. **Skill strength no longer overflows its card** (Shaked's complaint): the header wraps, long names wrap, the
   level word stays on its own line, and the side column can shrink. Verified in every screenshot.
5. **The plan on a phone.** Each row of "The plan until the interview" is a small card: day, skill in bold with its
   Start button beside it, mode and minutes, reason.
6. **The screenshot harness** (`apps/web/tools/screenshots/run.mjs`, `npm run screenshots`): starts the API with an
   in-memory store, a scripted grader and a stub for the login service, seeds two attempts and two interviews,
   builds the web app for production, injects a session, and photographs ten screens in two languages at 1280 px
   and at a true 390 px phone viewport through device emulation. It reports any sideways overflow, any screen whose
   main element did not render, and any console error. Signed-in screens can now be seen without a login.

## 3. What was verified

| Area | Check | Result |
|---|---|---|
| Evaluation engine | `git diff b9db3b1..HEAD -- backend/app/engine/` | no change; nothing in this stage touched evaluation or scoring |
| Backend code | `ruff`, offline test suite | clean, **794 tests pass** |
| Backend, real database | 17 live tests (rolled back), last run 00:46–01:08 with the machine awake | **12 passed; 4 lost their database connection mid-query** ("connection was closed in the middle of operation", "[WinError 10054] connection forcibly closed by the remote host"), all four in the longest transactions (two ten-question batches, the reseed, the interview); **1 real finding, fixed**: the HTTP-flow test still expected the feedback card in the submit response, which "grade first" (26 September) moved to a background task; the test now reads the attempt until the words arrive, as the web app does, and passes (73 s). No product assertion failed. The same tests passed 16 of 17 on 25 September, and the two real-model scripts on the same database passed tonight. To rerun from a stable network: `uv run pytest -v --timeout=900 tests/test_live_db.py tests/test_live_service.py tests/test_live_interview.py` |
| Real model, production rules | `scripts/e2e_live_trial.py` (weak answer → follow-up → focused next question; a 20-minute interview with a report) | passes, rolled back: the weak answer graded, its words written within 20 s, the follow-up asked, a focused next question chosen; the interview's three turns evaluated in 8 to 10 s each and the report in 12 s |
| Goal, program and XP on the real database | `scripts/e2e_goal_and_visuals.py` | passes, rolled back: the goal recorded, a program item started and answered by the real evaluator, a drawn circuit assessed and kept in the interview report |
| Web app | `tsc`, 49 unit tests, production `next build` (run by the harness) | clean, pass, builds |
| Every screen, both languages, both widths | the harness: 40 screenshots, checked by eye | no overflow, every screen rendered, no console errors |
| Interface guidelines | the changed files against the Vercel rules with JobRun's overrides | one fix: the access gate's buttons now carry an explicit type; the one physical `text-align: left` is on a code block that is `dir="ltr"` on purpose |
| Deploys | the Netlify workflow for each push; Render `smoke_http.py` with all 25 routes | the Netlify workflow succeeded for every push of the night; Render passes all 25 routes |

## 4. What the screenshots showed, and what changed because of them

- The practice screen was hiding its feedback panels in the harness because the scripted grader counted as demo
  mode; the harness now labels it as a model, and the grade ring, "what was good / what was missing", the tip, the
  follow-up and the next question all photograph.
- The phone plan table stacked five cells per row with the Start button on its own line; rebuilt as cards.
- The interview report's fit card showed "—" for an interview with no evidence; it says so in words now.
- Four headings and two subtitles still read as placeholders; rewritten.
- The sign-in shot waited for the old form's class; the harness now waits for the landing page's root.

## 5. Open, not fixed

- **Text that comes from data is not always in the interface language.** Skill names are English in the seed, a
  deterministic check's message ("6 of 8 specified rows differ") and the second line of some tips are English, and
  the plan's reasons are written in the language the plan was built in. These are content and backend strings, not
  interface strings; each is noted in §6 of STATUS as a follow-up.
- **The road-so-far chart is thin for a new user.** One bar after one day is correct but looks empty. A first-week
  treatment (a message instead of a chart until three days of answers exist) is a small follow-up.
- **Days are UTC** (unchanged from the last report): between midnight and 03:00 Israel time an answer counts for the
  previous day.
- **The speed guard in the live suite** (unchanged): listing the 30 questions right after a reseed takes about 5 s
  from this machine against a 3-s limit; warm it is 0.6 s and from Render much less.

## 6. For Shaked in the morning

1. Open https://jobrun-practice.netlify.app signed out, on your phone and on a computer, and look at the landing
   page. Then sign in and walk Learn → today's item → answer → the plan on the progress page. Say what still looks
   "made by a machine"; the brief's checklist is in `docs/design-brief-2026-09-27.md` §8.
2. From the speed night, still yours to do: set Render's `DATABASE_URL` to the Transaction pooler (port 6543);
   decide on the Anthropic tier; Opus stays the judge unless you say otherwise; rotate the database password.
3. Rotate the Netlify build hook that was pasted in chat, and update the GitHub secret `NETLIFY_PRACTICE_BUILD_HOOK`.
4. For night runs: keep the laptop plugged in and set Windows not to sleep on power ("Screen and sleep" → never
   when plugged in), or the live suite and any real-model script die mid-query when the machine enters standby.
5. Tell Harel about the new look before testers see it. His original design is saved as the git tag
   `design/harel-original`; the look before the Duolingo-style pass is `design/before-duolingo`.
