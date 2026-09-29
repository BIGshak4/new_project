# The interactive layer: what was added and how it was verified — 29 September 2026

Written for Shaked and Harel. After the look night (`docs/system-verification-2026-09-28.md`) Shaked asked for the
last ten percent of feel: how things move, open, close and confirm. Four libraries were added for that, each for one
job. The palette, type, copy and layout of the brief did not change, and nothing under `backend/` changed.
`backend/STATUS.md` §5p has the build notes.

## 1. What changed, screen by screen

- **Learn.** The path's nodes arrive one after another (45 ms apart, half a second at most). The current node
  breathes gently until it is pressed. When the page opens and today's node is below the fold, the page scrolls to
  it once. Skill strength bars fill from the start edge. The done tick pops in.
- **Practice.** The grade reveals itself in order: the ring draws, the glyph appears, the band pops, the XP pill
  pops, then "what was good", "what was missing" and the tip slide in, all inside a second and a half. The long
  paragraph about how hints affect the grade is now behind a "?" beside the hint buttons. "Saved to your account"
  and "added to this question's companies" are toasts.
- **Library.** The topic and job-type selects are proper menus: keyboard, type-ahead, Escape, focus return,
  right-to-left, the current value ticked.
- **Goal.** The seniority select is the same kind of menu; saving the goal shows a toast.
- **Everywhere.** The XP in the top bar counts up to its new total instead of jumping. Views cross-fade in 160 ms.
  The language switch is a menu with both languages listed and the current one ticked.
- **Reduced motion.** Motion's provider reads the system setting, and every animated piece also checks it, so a
  reader who asked for less motion gets none of this and still gets every screen.

## 2. The libraries and why these

| Library | Job | Why this one |
|---|---|---|
| Motion (`motion/react` 13) | springs, staggers, the counting number, the cross-fade | the standard for React motion; respects reduced motion; small when only `motion` and a few hooks are imported |
| Radix Select, Popover, Dropdown Menu | the menus and the "?" | unstyled, so they take the brief's look; accessibility and RTL handled; used by most serious React products |
| Sonner | toasts | tiny, one line to use, direction-aware |
| Recharts | the road-so-far chart | **not added yet**; planned for night 2 once there is more than a week of data to draw |

## 3. What was verified

| Area | Check | Result |
|---|---|---|
| Types and tests | `tsc`, `npm test` | clean; **54 tests** (5 new in `tests/ui.test.ts`: the select value mapping, the stagger cap, the grade order, the scroll rule, the counter) |
| Every screen | the harness, now **52 shots**: the original 40 plus a select open, the hint popover open and the language menu open, in both languages and both widths | no overflow, every screen rendered, no console errors; the layers open where they should and read correctly right-to-left |
| Production build | `next build` (the harness runs it) | builds; all client JavaScript chunks measured gzipped: **559 KB before, 653 KB after**, so the four libraries cost about 94 KB compressed (Motion is most of it). A visitor's first screen loads a subset of that; the pages were measured the same way in both builds |
| Backend | `git diff -- backend/` | nothing changed, so the engine, API and database were not re-run |
| Deploys | the Netlify workflow for the push | succeeded for the push (d1b96ab); the site is live with the new layer |

## 4. Found while photographing

- The two library selects took the whole toolbar row because the new trigger was full-width; they now sit in the
  row on a desktop and stack on a phone.
- The harness's settle wait was shorter than the grade sequence, so the first shots caught it mid-reveal; it now
  waits two seconds after the screen's main element appears.

## 5. Night 2, not started

Recharts for the chart; motion in the interview room (the timer, the change of turn); transitions between the
practice steps (answer → grade → follow-up → next question); a polish pass over every screen with fresh screenshots.

## 6. For Shaked

1. Open Learn on your phone and watch the path arrive and today's node breathe; answer a question and watch the
   grade come in. Say if anything moves too much. Everything can be tuned in one place (`lib/ui.ts`).
2. If you prefer less motion in general, the system setting "reduce motion" already turns it all off; say so and I
   can make it the default instead.
3. The earlier list still stands: Render's database URL to the Transaction pooler, the Anthropic tier, the password
   and hook rotations, Windows not sleeping while plugged in, a word to Harel.
