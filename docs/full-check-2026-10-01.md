# Full check after the Workbench: verification, profiling and review — 1 October 2026

Written for Shaked and Harel. Shaked asked for a complete pass over the system as it stands after the identity
change: every test suite, the real database and the real model, the deployments, the speed of the backend and of the
pages, and an independent read of the code that changed in the last three nights. This is the result. The
backend's code did not change in those nights, so its numbers here are a regression check against
`docs/performance-2026-09-26.md`.

## 1. Verification

| Area | Check | Result |
|---|---|---|
| Backend code | `ruff`, offline suite | clean, **794 tests pass** (18 s) |
| Backend, real database | 17 live tests (rolled back), run alone with a 15-minute cap per test | **17 of 17 passed in one run** (15 min 55 s, laptop awake, connection stable) |
| Real model, production rules | `scripts/e2e_live_trial.py` (weak answer → follow-up → next question; a 20-minute interview with a report) | passes, rolled back: the weak answer graded with the XOR-parity focus, the follow-up asked, a focused next question chosen; the three interview turns evaluated in 8–10 s each and the report (narrative generated) in 34 s; 100 s wall |
| Goal, program, XP, drawings | `scripts/e2e_goal_and_visuals.py` | passes, rolled back: the goal recorded, a turn answered with a drawn circuit and assessed (`circuit_assessed`, 8 visual parts stored), the band and drawing in the report; 60 s wall |
| Web app | `tsc`, `npm test`, production build | clean, **56 tests**, builds |
| Every screen | the harness: 52 shots, both languages, 1280 and 390 px, with menus and popovers open | **no overflow, every screen rendered, no console errors** |
| Render | `/health?db_check=true`, `scripts/smoke_http.py` (25 routes) | healthy, **on the Transaction pooler now** (Shaked's change), round trip **3.0 ms**; all 25 routes pass |
| Netlify | the deploy workflow | green for every push of the night |

## 2. Profiling

### The backend

| Measure | 26 September | Today |
|---|---|---|
| Full practice loop in memory (`profile_service.py --cpu`, 200 loops) | — | **48 ms per loop**; the top of the profile is the in-memory store's profile copy, which the database store does not have; XP summary 2.5 ms |
| Grade latency on the real model (`latency_bench.py`) | 8.1 s median, 10.3 s max (from this machine) | **7.9 s median, 10.3 s max** grade known (5 answers, real model, from this machine); evaluator 5.0 s median; all feedback 17.9 s median; submit 21 statements, progress 12. Identical to 26 September within noise |
| Many users (`load_test.py`, local API over HTTP, scripted model with real timing) | 10/50/100 users, all flows complete, event-loop lag p99 ≤ 29 ms | **10 and 50 users: every flow completed, no errors**, event-loop lag p50 4.8 ms / p99 27 ms at 50 users, memory 117 → 140 MB, submit p50 7.9 s and follow-up 8.4 s with the scripted model's 8-second latency (the API adds about 10 ms of its own); reads 6–15 ms p50. No regression against 26 September |

### The pages (the harness, production build, local, headless Edge)

| Measure | Desktop 1280 | Phone 390 |
|---|---|---|
| First contentful paint, median (worst) | 60 ms (128 ms on the cold first page; 492 ms before the fonts were self-hosted) | 48 ms (64 ms) |
| Largest contentful paint, median (worst) | 120 ms (352 ms) | 104 ms (284 ms) |
| Layout shift, worst | 0.27 before the fixes below, **0.079 after** | 0 |
| JavaScript transferred on the first page | 434 KB compressed | same |
| Heap after render | 14 MB | 15 MB |

All of that is far inside the "good" band (paint under 1.8 s, shift under 0.1) except the desktop layout shift on
screens whose content arrives after a fetch (Today, the interview report). The loading states of those two screens
now hold the room their content will take, and the page's main area is at least one screen tall so the new footer
never sits inside the first screen and gets pushed down when data arrives (that push was most of the shift). After
both: **worst shift 0.079 on desktop, 0 on the phone, no screen over 0.1**.

## 3. Independent code review (front end, commits since the interactive layer)

A second agent read every front-end file that changed in the three nights (Motion, Radix, Sonner, Recharts, the
Workbench) and confirmed nothing under `backend/app` changed. **No high-severity defect.** Fourteen medium and low
findings, all verified in code and all fixed in this pass:

1. **Title with a topic when the goal was incomplete**: the highlighted topic could appear under "Let's build your
   plan" because the backend fills the next item regardless of the goal. Gated on the goal.
2. **The timer announced every second** to screen readers in its last minute (`aria-live` on a ticking number). The
   timer is silent; a hidden status speaks once at one minute and once at ten seconds.
3. **The corner stamp was English in the Hebrew page** and showed the goal's minutes instead of today's remaining
   minutes. Every word goes through the translation function; it shows the minutes due today.
4. **The grain overlay used a blend mode over the whole viewport** at the top of the stacking order: a re-blend on
   every scroll frame on phones, and it sat above the menus. It is a plain alpha overlay now, under the menus, and
   off on phones.
5. **Five font families through a render-blocking import**, one of them (Heebo) redundant. The four faces are
   self-hosted through `next/font` with no run-time request to Google; Heebo is gone.
6. **"Yesterday" was computed in UTC**, two days back for an Israeli user between midnight and 03:00. Local date.
7. **The skill label was forced left-to-right** even when the server localised it to Hebrew. Direction is automatic.
8. **Monospace outside the stamp** (the skill label, the sketch labels). The label is in the text face; the sketch
   labels are hand-lettered.
9. **Labels on plain divs** that assistive technology ignores. The stamp is a note, the trace a group.
10. **The trace's strokes squashed on phones** (a stretched SVG). Non-scaling strokes.
11. **A select with a value not yet among its options rendered blank.** It shows its label as a placeholder.
12. **A dead helper with a live test** (the scroll rule). The helper carries the one rule and the test covers it.
13. **Phone probes at 42 px** with 10 px captions. 44 px and 11–12 px.
14. **The chart wrapper hid Recharts' keyboard layer** (`role="img"`). It is a figure with a label.

The reviewer's larger note: the stylesheet now carries two palettes, the Workbench overriding the earlier green
rules rather than replacing them (a focus ring and a tooltip still reached the old green through the mapped
tokens). Both were repointed; a pass to retire the old token names is the next hygiene task.

## 4. What was fixed in this pass

- The fourteen review findings above.
- Two loading states (Today, the interview report) now hold the room their content takes, for the layout shift.
- The harness records first paint, largest paint, layout shift, load time, script bytes and heap per screen, and
  prints a summary per width; `index.json` carries the numbers.

## 5. Still open

- The content that is not in the interface language (English skill names, check messages, tip second lines, plan
  reasons in the plan's language). A content pass, not a code fix.
- The live suite's 3-second listing guard is tight from this machine (0.6 s warm; the cold reseed path is slower
  over a 200 ms link). Not visible from Render.
- The bank covers 14 of the role's 27 skills with a primary question; the 30 questions stay "in review" until an
  engineer signs them off.

## 6. For Shaked

1. The Transaction pooler is live on Render: done, thank you. Still yours: the Anthropic tier, the database password
   and Netlify hook rotations, and Windows not sleeping while plugged in.
2. Look at the site on your phone signed in; the numbers above say it is fast, only your eyes say whether it feels
   right.
