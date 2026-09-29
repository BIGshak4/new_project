# The Workbench identity: what was rebuilt and how it was verified — 1 October 2026

Written for Shaked and Harel. On 30 September Shaked chose a new identity from four mockups and refined it in three
rounds: the Workbench, an engineer's bench with graph paper, navy ink, one signal yellow, copper for the coach's
hand, an editorial serif for headlines, rounded and aligned geometry, and hand-made touches (sketches, margin
notes, a sticky note, a highlighter, a sign-off). The brief is `docs/design-brief-2026-09-30-workbench.md`. This
night moved the whole web app onto it. Front-end only; the engine, the API and the database are untouched.
`backend/STATUS.md` §5r has the build notes.

## 1. What changed, in the order a user meets it

- **The landing page**: navy header, the serif headline with the highlighter under "today's practice", the sample
  question as a sheet with the MUX sketch beside it, the facts, the three steps, the sign-in sheet, the sign-off.
- **The shell**: a navy header with a yellow active tab and the wordmark's "run" in yellow; on a phone the same in
  the bottom bar; the pilot line as a copper margin note; on every page a footer signed by the two of you with one
  true sentence.
- **Today (was "Learn")**: rebuilt around the day. A kicker with your name, the job and the interview date; a serif
  title that names today's topic with a highlighter under it; a corner stamp in monospace (items, minutes,
  yesterday's band, streak); the day's sheet with a tag, the subject's sketch and its handwritten caption, the
  plan's reason and one sentence per mode, a button that says how long it takes ("ארבע דקות. קדימה"); today's items
  as round probes on a signal trace whose completed part is yellow; the rest of the week as a quiet list; a side
  column with today's hatched bar and a copper note, skill strength with navy blocks and copper for today's skill,
  the streak as a serif number, and the coach's sticky note with tomorrow's first item.
- **Practice**: the question sheet carries the subject's sketch in its corner; grades read green (strong), yellow
  (partial), copper (needs work); the tip is a copper-edged note.
- **Library, progress, interviews, report**: the same tokens and type; the chart in green, yellow, copper and the
  sea-blue level line; the timer in yellow, then orange, then red.
- **Sketches**: seven wobbly-line drawings keyed by subject (a MUX, two states with an arrow, a clock with setup and
  hold, a ripple of adders, an `always` block, an array with an index, a page of notes), each with a handwritten
  caption. Decorative, hidden from screen readers, hidden on phones where there is no room.

## 2. What did not change

The engine, the API, the database, XP, the plan router, the flows, the structure of the screens, and the four
libraries from the previous nights (Motion, Radix, Sonner, Recharts), which were restyled, not replaced. The green
Path look is saved as the git tag `design/path-green`; Harel's original as `design/harel-original`.

## 3. What was verified

| Area | Check | Result |
|---|---|---|
| Types and tests | `tsc`, `npm test` | clean; **56 tests** pass (no engine or API change, so the backend suites were not re-run) |
| Every screen | the harness, 52 shots, both languages, 1280 and 390 px | **52 shots, no overflow, every screen rendered, no console errors** on the fifth and final round; the earlier rounds each caught what the previous one showed (§4) |
| Production build | `next build` (the harness runs it) | builds; client JavaScript **755 → 759 KB gzipped**: the identity is CSS, SVG and three Google Fonts, not code |
| Backend | `git diff -- backend/` | only the harness seed (`tools/screenshots/run.mjs` on the web side; nothing under `backend/app`) |
| Deploys | the Netlify workflow for the push | succeeded for the push (dc1ea7f); the Workbench is live at https://jobrun-practice.netlify.app |

## 4. Found while photographing

- **The header stayed white** after the first pass: an older rule set the surface colour later in the file. The
  navy is now forced for the app header and the landing header alike.
- **The landing sample card still tilted** (a leftover from the previous brief); straightened, with the MUX sketch
  beside the question instead.
- **Long Latin skill names** ("Blocking and Non-blocking Assignments") widened the phone: the highlighted topic
  in the title, the sheet's title and the sticky note now break words when they must.
- **The handwritten margin note** quoted the plan's reason even when the plan was built in the other language;
  it now appears only when the reason is in the page's language, and only when it is short enough to read as a note.
- **The page scrolled the title away** on phones because the day's sheet always starts below the fold; it now
  scrolls only when the sheet has not even begun inside the first screen.
- **"1 items"** in the today note; singular fixed in both languages.
- **The seed** answered the program item, so Learn never photographed a current item; it now leaves the item open
  and the sheet shows "Continue where you stopped" with the yellow probe.

## 5. Open

- **The address.** The app keeps the plural ("אתם"); the mockups used the singular for punch. Switching touches every
  string and is a product decision.
- **Latin skill names** in the handwritten sticky note look less hand-written than the Hebrew around them; a Hebrew
  content pass for skill names (already on the list) fixes that too.
- **The trace** shows today's items only; a day with one item shows one pulse. That is honest, if quiet.

## 6. For Shaked

1. Open the site signed out and signed in, on the computer and on your phone, and say what still reads as made by a
   machine. The checklist is §9 of the brief.
2. Everything else on your list from the earlier reports still stands.
