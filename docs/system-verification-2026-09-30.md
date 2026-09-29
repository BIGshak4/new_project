# Night 2 of the interactive layer: the chart, the interview room, the practice flow — 30 September 2026

Written for Shaked and Harel. Night 1 (`docs/system-verification-2026-09-29.md`) added Motion, Radix and Sonner.
Night 2 finishes the plan: Recharts for the chart, motion in the interview room, the practice steps flowing into
each other, and a polish pass over every screen. Front-end only; the only change under `backend/` is the harness's
seed. `backend/STATUS.md` §5q has the build notes.

## 1. What changed

- **"The road so far."** From the third practice day it is a real chart: stacked bars per day in the brief's colours
  (needs work, partial, strong), the average level as a line on its own axis once two days have a level, and a
  tooltip per day that says "3 answers · 0 strong, 1 partial, 2 to strengthen · level 2.4" in the page's language.
  The bars grow in on first view. Days one and two keep the sentence from the look night. A single level point is
  not drawn (a lone dot read as a mistake).
- **The interview room.** A new question slides in from the reading side when the turn changes, and the answer box
  clears with it. The timer turns orange for the last minute and red, beating once a second, for the last ten
  seconds. In the report the fit cards and the turn cards arrive one after another and the XP pills pop.
- **The practice flow.** When the grade arrives the page brings the feedback into view once. The open follow-up
  slides in, the answered follow-up's band and XP pop, and the next-question card slides in after them, so the four
  steps read as one flow instead of blocks appearing.
- **An honest report.** "No clear gaps, well done" now needs at least three assessed skills; below that the report
  says there are not enough answers yet to point at gaps.
- **Reduced motion** still turns every piece off, including the chart's growth and the timer's beat.

## 2. What was verified

| Area | Check | Result |
|---|---|---|
| Types and tests | `tsc`, `npm test` | clean; **56 tests** (2 new: the timer's tone thresholds, the chart rows) |
| Every screen | the harness, 52 shots, now seeded with three practice days and a three-turn interview | no overflow, every screen rendered, no console errors, both languages and widths; the chart shows three days in the right colours (strong, partial, needs work) and the report four turns with their bands and XP |
| Production build | `next build` (the harness runs it) | builds; all client chunks gzipped **653 KB before, 755 KB after**: Recharts costs about 100 KB compressed, which is the price of a real charting library. If that matters later, the chart can be loaded only on the Progress page (a dynamic import) and the rest of the site would not pay for it |
| Backend | `git diff -- backend/` | only `scripts/screenshot_server.py` (the harness's backdate route and grader markers); the engine, API and database untouched |
| Deploys | the Netlify workflow for the push | succeeded for the push (b881cbd); the site is live |

## 3. Found while photographing

- **The timer's warning looked like its normal state.** The interview timer already sits in a yellow pill (yellow is
  the interview's colour), so an amber "last minute" was invisible; the last minute is orange, the last ten seconds
  red.
- **A lone level point.** With one day of level history the chart drew a single blue dot that read as a mistake;
  the line now appears only once two days have a level.
- **The seed's earlier days all came out "needs work".** The automatic truth-table check caps the band when the
  expression is wrong, whatever the grader says, so the harness's backdated answers now carry the right expression.
  A good reminder of how the engine works, not a change to it.
- **"No clear gaps, well done" after one assessed skill.** The report said it whenever the recommendation list was
  empty; it now needs at least three assessed skills.
- **The harness's backdate route looked up attempts on the wrong object** (a leftover from the store's older
  shape) and answered 500; fixed and covered by a quick local call.

## 4. What is next

The interactive layer is complete as planned. What remains needs people rather than code: Harel's review of the
new look, a few testers on their phones, Render's database URL on the Transaction pooler, the Anthropic tier, the
two rotations, and the content pass for the strings that come from data in English (skill names, check messages,
tip second lines).

## 5. For Shaked

1. Open Progress after three days of answers and hover or tap the bars. Open a mock interview and let the last
   minute run down to see the timer. Answer a question and watch the flow from grade to next question.
2. Say if anything moves too much; all timings live in one file (`apps/web/src/lib/ui.ts`).
