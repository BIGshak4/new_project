# Design brief: Workbench — 30 September 2026

The identity Shaked chose on 30 September from four mockups (`docs/design/mockups-2026-09-30/`), after three rounds
of changes to the Workbench direction: softer geometry, an editorial serif instead of a condensed face, round
probes instead of squares, no tilts, and the hand-made touches. This brief replaces
`docs/design-brief-2026-09-27.md` for everything visual. The engine, the API, the flows and the structure of every
screen stay as they are; this is the skin, the type and the voice.

## 1. The idea in one line

An engineer's workbench: graph paper with a little grain, navy ink, one signal-yellow trace, copper for the warm
notes, and a coach who writes in the margins by hand. Tidy, not sterile. Made by two people, and it says so.

## 2. Palette (own colours, not borrowed)

| Token | Hex | Job |
|---|---|---|
| `--ink` | `#0f1b2d` | text, the trace when active, primary buttons |
| `--ink-2` | `#2a3a52` | secondary text, sketches |
| `--mute` | `#5d6b80` | captions, labels (4.5:1 on paper) |
| `--paper` | `#f3f4ef` | page background, with the grid and grain |
| `--sheet` | `#ffffff` | cards ("sheets" and "panels") |
| `--line` | `#cfd5de` | card borders, inactive trace, dividers |
| `--grid` | `#e9ebe4` | the graph-paper lines |
| `--navy` / `--navy-deep` | `#14213d` / `#0c1428` | header, primary button, skill blocks |
| `--signal` / `--signal-deep` | `#ffb703` / `#c98a00` | the one loud colour: current item, active tab, highlighter, XP, the button's 3D shadow |
| `--copper` / `--copper-soft` | `#b5651d` / `#f6e3d3` | streak, handwritten notes, the skill being trained today |
| `--ok` / `--ok-soft` | `#1b7f4e` / `#dff2e7` | done, strong answers |
| `--warn` / `--warn-soft` | `#c2410c` / `#ffedd5` | needs work, the timer's last minute |
| `--danger` / `--danger-soft` | `#b42318` / `#fee4e2` | errors, the last ten seconds |
| `--sea` | `#1c64b8` | "needs a refresh", the level line in the chart, focus rings |
| sticky | `#fff3b0` | the coach's sticky note |

Rules: yellow is never a background for text blocks, only a pill, a stroke or a shadow. Green means done. Copper means
the human hand (notes, streak). No gradients as decoration. No pure black.

## 3. Type

- **Headlines and big numbers:** Frank Ruhl Libre 700 (900 for the wordmark and the streak number). Hebrew and Latin
  in the same face. Sizes: page title 44–50 px desktop, 32–34 phone; card titles 26–30; panel titles 20.
- **Everything else:** Assistant 400–800. Body 16 px / 1.55, captions 13.
- **Numbers that belong to the bench** (the corner stamp: day 3 of 12, items, minutes): JetBrains Mono 500, and
  nowhere else. Monospace labels everywhere read as a machine.
- **Handwriting:** Amatic SC 700, copper, for the coach's asides only: one margin note per screen at most, the sticky
  note, the sketch caption, the sign-off. Never for information the user must read to act.
- No all-caps, no tracked-out text, no single coloured word in a headline. The highlighter stroke (yellow, 55 %
  opacity, straight, under the key phrase) is the one emphasis device.

## 4. Geometry and depth

- Radii: sheets 22 px, panels 18 px, inputs 14 px, pills and buttons 999 px, probes and nodes circles.
- Borders: 2 px `--line` on sheets and panels. Depth from a soft navy shadow (`0 18px 40px -26px rgba(20,33,61,.45)`),
  never grey `rgba(0,0,0,.1)`.
- The primary button: navy, white text, `0 6px 0 var(--signal-deep)` shadow, lifts 1 px on hover and presses 5 px on
  :active. Secondary buttons: white with a `--line` border. Text buttons: navy, underline on hover.
- Everything aligned. No rotations, no skew. The hand-made feeling comes from texture and drawings, not from tilt.
- The page: `--paper` with a 32 px graph-paper grid and a fixed grain overlay (SVG turbulence, 35 % multiply).
- The header: navy, light text, the active tab a yellow pill, the wordmark in the serif with "run" in yellow.

## 5. The hand-made layer (what makes it human)

1. **A sketch per subject**, drawn as wobbly-line SVG (turbulence displacement, 2 px): a MUX for combinational logic,
   two state bubbles with an arrow for state machines, a clock with setup/hold arrows for timing, a ripple of full
   adders for arithmetic, an `always @(posedge clk)` block for HDL, an array with an index for code. It sits beside
   the question of the day and in the corner of the question sheet, with a handwritten caption.
2. **One margin note** in handwriting with an arrow, above the day's card: the plan's own reason for the item.
3. **The sticky note** in the side column: tomorrow's first item ("מחר: Boolean · שאלה קצרה · 4 דק׳"), with a strip of
   tape, straight.
4. **The highlighter** under the key phrase of the page title.
5. **The corner stamp** in monospace: day N of M until the interview, items and minutes today, yesterday's band.
6. **The sign-off** at the foot of every page: "שקד והראל" in handwriting, then one true sentence: two engineering
   students who sat through too many interviews and built the tool they wanted before the first one; an engineer
   checks every question before it reaches you.
7. **The trace**: today's items as a signal line with round probes; the completed part of the line is yellow, the rest
   `--line`. Future days are a quiet list under it, not more nodes.

## 6. Voice

Dry, personal, specific. Engineer to engineer, with warmth in the facts rather than in adjectives.

- Name the user in the kicker. Name the topic in the title. Quote the question when it is known; describe it when it
  is not.
- Say why today's item matters for the interview, in one sentence, from the plan's reason. Never invent claims about
  interviewers or companies.
- One short sentence of attitude per block, never two: "אין פה טריק, יש פה דיוק." "שלושה ימים שלא ויתרת."
- Numbers only where they change what the reader does next.
- Buttons say what happens: "ארבע דקות. קדימה", "לשאלה הבאה", "שמירה".
- Errors say what happened and what to do, in the app's voice, no apology.
- Grammar: the app keeps the plural address ("אתם") it uses today, which is neutral; the mockups used the masculine
  singular for punch. Switching is a product decision for Shaked and would touch every string; not part of this
  rebuild.

## 7. Screens, what changes

- **Shell:** navy header and phone tab bar; the pilot line becomes a quiet copper margin note; the sign-off footer.
- **Learn:** the Workbench layout from the mockup: kicker, serif title with the highlighter, corner stamp, the day's
  sheet (tag, question or description, why today, CTA), the trace with probes, "later this week" list, side panels
  (today with the hatched bar, strength with navy blocks and copper for today's skill, streak with the serif number,
  the sticky note).
- **Practice:** the question sheet gets the subject sketch in its corner and the serif title; the grade panel uses
  ok/warn/signal; the saved-answer card and the feedback flow keep their motion.
- **Library, progress, interview, report:** tokens and type; the chart in navy/signal/copper/ok; the timer in yellow,
  then warn, then danger.
- **Landing:** the same bench: navy header, serif headline with the highlighter, the sample question as a sheet with
  the MUX sketch, the facts as a stamp block, the three steps as probes on a trace, the sign-in sheet, the sign-off.

## 8. Not in scope

The engine, the API, the database, the XP rules, the plan router, the copy structure of the flows, Radix/Sonner/
Recharts/Motion (they stay and are restyled). Harel's original design stays under `design/harel-original`; the
green Path look is tagged `design/path-green` before this rebuild.

## 9. The reviewer's checklist (what "looks made by a machine" here)

Grey-bordered white cards on cream; all-caps eyebrows; monospace labels outside the stamp; a single coloured word in
a headline; gradients as decoration; tilted elements; the same radius on everything; emoji; "Welcome back" copy;
a footer with a copyright line instead of people.
