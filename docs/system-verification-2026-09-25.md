# System verification after the XP and Duolingo-style night — 25 September 2026

Written for Shaked and Harel. The night built two things. The first is XP: points for every answer, computed from
results the engine already stores, without changing how answers are evaluated. The second is a full restyle of the
site in the approved "Path" direction. Afterwards the whole system was verified from scratch.
`backend/STATUS.md` §5m has the build notes.

## 1. How the night went

- **Built by a Fable agent, then continued on Opus 5.5.** The first Fable run stalled early; resumed, it finished the
  build in three commits (`1ff9aba`, `1f528ed`, `eab9ff4`). Later the Fable usage limit was reached during the review,
  so, as Shaked asked, the review and the rest of the verification ran on Opus 5.5.
- **The network dropped for part of the night.** One live-suite run took 1 h 49 m with connection errors, and the first
  reviewer died on a DNS failure. Both were rerun once the connection was back. The numbers below come from the reruns.
- **The API on Render stopped answering for about an hour.** Requests connected but never got a reply, while Render's
  status page reported no incident. The same code started and passed every check locally, so the running instance was
  stuck, not the code. A push triggered a fresh deploy, and that brought it back. There is no Render access from this
  machine (no deploy hook or API key), so a push was the only restart available.

## 2. What was verified

| Area | Check | Result |
|---|---|---|
| Evaluation engine | `git diff cd37654..HEAD -- backend/app/engine/`, plus a test that runs the same flow with XP zeroed out and compares the engine's band, levels, loyalty, overview and stored `engine_state` | only the new `xp.py` was added; the engine's results are identical with and without XP |
| Backend code | `ruff`, **776 offline tests** (34 new for XP and the review fixes) | clean, all pass |
| Backend, real database | 17 live tests (rolled back), rerun on a stable connection | **16 passed**; the 17th is a speed guard, see §4 |
| XP on the real database | `scripts/e2e_goal_and_visuals.py`: a program item is started, answered with the reference by the real evaluator (STRONG), the item is ticked, the overview shows **+24 XP** today and a 1-day streak. The interview XP reader was run read-only against real users | passes, rolled back |
| Real model, production rules | `scripts/e2e_live_trial.py`: weak answer → one follow-up → focused next question; a 20-minute interview on trial questions with a generated report | passes, rolled back |
| Web app | `tsc`, **49 unit tests** (11 new for the path), `next build` | clean, pass, builds |
| Phone layout | the live sign-in page at a true 390 px viewport, through device emulation (headless windows cannot be narrower than about 500 px, so a plain screenshot misleads) | fits exactly, no sideways scroll, Hebrew right-to-left correct |
| Deploys | the Netlify workflow for every push; Render `smoke_http.py` with all **25** routes | all succeeded; smoke passes after the recovery |
| Independent review | a second agent (Opus 5.5) read the whole diff and ran the offline suites | 14 findings, none touching evaluation or scoring; the important ones fixed (§3) |

## 3. Found and fixed

1. **A Start button that could not start.** When today's items were done, the Learn path made tomorrow's first item
   "current" and offered Start, which the server refuses. Now only the program's own next item is current. When today
   is done, a "done for today" line and a library link are back, as the old panel had them.
2. **XP gave away hidden interview results.** Interview bands stay hidden until the interview ends, but XP counted
   each turn as soon as it was scored, so the top bar jumped by an amount that revealed the band. XP now counts only
   finished interviews.
3. **Skills credited with XP the engine never credited them.** A follow-up and an interview turn are evidence on the
   primary skill only in the engine, but XP split them over every skill of the question. They now credit the primary
   skill only.
4. **Demo environments showed XP, streak and level derived from demo grades,** which are hidden everywhere else. They
   are now hidden too.
5. **Smaller fixes.** XP rounds half up like the engine. XP totals are all time instead of a rolling year. The
   interview reader reads three JSON fields instead of the whole turn record. Today's own items no longer show
   "carried" after a same-day rebuild, and the flag compares one clock. Faint text was darkened to 4.5:1 contrast.
   The progress bar and the top-bar numbers have spoken names. The library's view switcher uses pressed buttons.
   The path draws items in the server's order.

## 4. Open, not fixed

- **The speed guard in the live suite.** Listing the 30 questions right after reseeding took 4.8 to 5.8 seconds from
  this machine, against a 3-second limit. Measured separately, a warm listing takes 0.6 to 0.7 seconds. The company
  tags added two nights ago cost one more database round trip (0.2 to 0.4 seconds from here). The cold path makes
  about ten round trips, and tonight's connection took 200 to 390 ms per round trip. On Render the database is much
  closer, so this is not visible to users. Still, the guard is a real signal: merging the company-tag lookup into the
  question query would remove that extra round trip.
- **Days are UTC.** The streak, today's XP and the program's "today" all use UTC dates, which is consistent on the
  server, where the clock is UTC. For an Israeli user it means that between midnight and 03:00 local time, an answer
  counts for the previous day. The proper fix is to send the user's time zone and group by it.
- **Not seen in a browser while signed in.** The Learn page, the practice screen and the progress page need a login
  to render, so the review checked their layout in code: every class has styles, no fixed width is wider than 390 px,
  and the path and layout mirror right-to-left. Only the sign-in page was photographed.
- **XP ignores follow-up difficulty.** XP uses the question's difficulty even for a follow-up, whose own difficulty
  may differ. The effect is small, and it is documented in `xp.py`.
- **Not changed:** `level_progress` (the fill of a skill's bar toward its next level) is served but not drawn yet.
  The Learn page's bars show the level.

## 5. For Shaked in the morning

1. Open https://jobrun-practice.netlify.app on your phone and on a computer. Try Learn (the path), start today's
   item, answer it, and watch the XP and the next step. Then say what feels off.
2. Tell Harel about the new look before testers see it. His original design is saved as the git tag
   `design/harel-original`.
3. Rotate the Netlify build hook that was pasted in chat (still open from before).
