# JobRun design brief — 27 September 2026

The binding brief for the practice web app (`apps/web`). Written after the founders approved the "Path" direction
(Duolingo-inspired: gamified, friendly, clean) and asked for two more things: make it feel premium, and make it look
like a real product, not a page an AI generated. Where this brief pins an axis (colour, type, geometry, copy), it wins
over the installed design skills (`.claude/skills/frontend-design`, `.claude/skills/web-interface-guidelines`); where it
leaves an axis free, those skills apply.

## 1. Who and what

- **Product:** an AI interview coach for electrical-engineering and software students in Israel preparing for their
  first hardware or software job. It asks real interview questions, grades the answer in about eight seconds, asks
  one follow-up, and keeps a plan until the interview date. Hebrew first, right-to-left, with an English mode.
- **The audience** is 22 to 28, technical, anxious about interviews, practising on a phone between classes and on a
  laptop in the evening. They know Duolingo and LeetCode. They distrust "AI slop".
- **The primary job of every screen:** get the person to answer the next question, and show honestly where they stand.
- **The one memorable thing:** the path. Everything else stays quiet.

## 2. Palette (our own; never Duolingo's #58CC02 / #1CB0F6, never their owl, name or font)

| token | hex | use | contrast |
|---|---|---|---|
| `--paper` | `#F6F5EF` | page ground (warm off-white) | |
| `--surface` | `#FFFFFF` | cards | |
| `--line` | `#E6E3D8` | 2 px card borders | |
| `--ink` | `#23302A` | text | 13.6:1 on paper |
| `--muted` | `#55635B` | secondary text | 6.5:1 on paper |
| `--green` | `#2F9E44` | nodes, meters, icons; never under white text | 3.3:1 on white (UI only) |
| `--green-button` | `#22823A` | filled buttons with white text | 4.9:1 |
| `--green-deep` | `#217A33` | the pressed 3D shadow | |
| `--green-text` | `#1F7A34` | green text on white | 5.0:1 |
| `--green-soft` | `#E7F5E9` | tinted grounds | |
| `--blue` | `#1C64B8` | "needs a refresh", links, the secondary button | 6.3:1 on white |
| `--blue-soft` | `#E3EEFB` | tinted grounds | |
| `--orange` / `--orange-text` | `#F97316` / `#C2410C` | streak flame; orange text | 4.6:1 |
| `--yellow-soft` / `--yellow-text` | `#FFF4D6` / `#A16207` | interview nodes and cards | 5.2:1 on the soft |
| `--purple-soft` / `--purple-text` | `#EDE9FE` / `#5B3FBF` | XP badges and the "+N XP" moment | 6.0:1 on the soft |
| `--danger` | `#B42318` | errors | 6.4:1 on white |

Rules: one primary (green), one secondary (blue), three accents (orange for streaks, yellow for interviews, purple
for XP). Never two accents in one component. No gradients on text, no gradient washes, no glows, no decorative
blobs. Shadows are soft and coloured like the element they sit under (`0 6px 18px -10px` of the element's deep
colour at 40–60 %), never plain black.

## 3. Typography

- **Latin:** Nunito 600/700/800/900 (Google Fonts). **Hebrew:** Assistant 600/700/800 (Google Fonts; rounder than
  Heebo and closer to Nunito's warmth; Nunito has no Hebrew glyphs). Stack: `Nunito, Assistant, system-ui, sans-serif`.
- Scale (px / line-height / weight): display 44/1.1/900 (landing only) · h1 32/1.2/900 · h2 22/1.3/800 ·
  h3 17/1.35/800 · body 15/1.6/600 · small 13/1.5/600 · caption 12/1.4/700. On phones h1 is 27 px.
- Headings are extra-bold and chunky, sentence case, no letter-spacing tricks, no all-caps eyebrows, never one
  word coloured or italicised inside a heading. Body copy under 70 characters a line.

## 4. Geometry and motion

- Radii: cards 24–28 px, buttons 18 px (pills only for chips and the top-bar stats), inputs 14 px, nodes round.
- Borders: 2 px `--line` on cards; inputs 2 px `#BCC9BF`, focus ring 3 px `--green-button` at 25 %.
- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 64. Cards breathe: 24–32 px padding on desktop, 18–20 px on phones.
- **The 3D button:** filled ground, `box-shadow: 0 5px 0 <deep>`; on `:active` `transform: translateY(5px)` and the
  shadow goes to 0; hover lifts 1 px with the shadow at 6 px. Text buttons and icon buttons stay flat.
- **Hover on cards:** `transform: translateY(-2px)` with `transition: transform 260ms cubic-bezier(.34,1.56,.64,1),
  box-shadow 200ms` (a slight bounce), only on cards that are links or buttons; a static card does not move.
- **Motion budget:** one orchestrated moment per screen (the path node that becomes current, the "+N XP" pill,
  the grade appearing). No page-load fade-and-slide on sections. `prefers-reduced-motion` turns all of it off
  (already in globals.css; keep it).
- Touch targets 44 px or more. Visible keyboard focus everywhere.

## 5. Components

- **Top bar** (desktop): wordmark, four tabs, streak flame + days, XP + level word, language switch, sign out.
  Active tab is a filled soft-green pill. **Bottom tab bar** (under 760 px): four icons with labels, 64 px tall,
  safe-area padding.
- **Cards:** white, 2 px border, 24 px radius, soft coloured shadow only when the card is interactive.
- **Stat tiles:** the number big (26–30 px, 900), the label small under it; no icons inside tiles.
- **Meters:** 12–18 px tall, rounded, `--green` fill on `--line-soft` track; segmented bars are five blocks with 4 px gaps.
- **Badges:** 12 px, 700, rounded 999; one per line at most.
- **Path nodes:** 72 px (current 88 px) round, 3D shadow of their colour; done green with a tick, current green with
  a play icon and the Start button beside it, locked `--grey-node` with a lock, interview yellow with a microphone.
- **Feedback panels:** "What was good" on `--green-soft`, "What was missing" on `--yellow-soft`, the tip on white
  with a bulb; the band ring and the "+N XP" purple pill in the header.
- **Forms:** label above, 14 px radius input, one primary button, the secondary action as a text button.
- **Tables:** no zebra stripes; 2 px `--line-soft` row lines; the row's action at the end.

## 6. The landing page (sign-in)

Open with the most characteristic thing in this product's world: **a real interview question**, not a slogan.
Layout (desktop): a header (wordmark, language, "Sign in"); a two-column hero with the headline and a sample
question card that looks exactly like the practice screen's question sheet ("Three sensors guard a room. Build the
alarm that fires when at least two agree." with the grade ring and "+18 XP"); under it a stats strip of **true
product facts only**: 30 questions · 6 subjects · 6 job types · Hebrew and English · a grade in about 8 seconds ·
mock interviews of 20, 30 or 45 minutes; then the main action area: the sign-in / create-account card. On phones the
question card comes after the headline, the form last. Nothing invented: no testimonials, no logos, no counts we
do not have.

## 7. "Does not look AI-made": the rulebook

Tells to remove wherever they exist: generic hero copy ("Unlock your potential", "Level up your skills");
gradient text; purple or neon glows; three identical cards in a row with an icon, a title and two lines; emoji used
as icons; everything centred; ALL-CAPS eyebrow labels above headings; meta strings joined with " · " where a
sentence would do; a "→" glued to every button; the same border-radius and the same grey shadow on everything;
lorem-like sentences ("Focused hardware and software interview practice. At your pace.").

Do instead: write like a coach who knows the field (concrete nouns: counters, setup time, a testbench, a follow-up);
use real numbers from the person's own data; let cards differ in size and weight by importance; left/start-align
text; one motif (the path) carried through (nodes, meters, the tick); lucide icons only, one stroke width;
sentence case; buttons that say what happens ("Start today's question", "Send answer", "Save my goal").

Ten copy examples (Hebrew / English):
1. Learn h1: "הדרך שלכם, 12 ימים לראיון" / "Your path, 12 days to go"
2. Current node button: "מתחילים" / "Start"; an item already begun: "להמשיך" / "Continue"
3. Done for today: "להיום סיימתם. מחר: מכונות מצבים." / "Done for today. Tomorrow: state machines."
4. Feedback good: "מה היה טוב" / "What was good"; missing: "מה היה חסר" / "What was missing"; tip: "לפעם הבאה" / "For next time"
5. Follow-up waiting: "כותבים לכם שאלת המשך…" / "Writing your follow-up question…"
6. Next question card: "השאלה הבאה מחכה" / "Your next question is ready"
7. Landing headline: "הראיון הבא מתחיל בתרגול של היום." / "The next interview starts with today's practice."
8. Landing sub: "שאלות אמיתיות מראיונות חומרה ותוכנה, ציון תוך שניות, ותוכנית עד יום הראיון." /
   "Real hardware and software interview questions, a grade in seconds, and a plan until interview day."
9. Empty library: "אין שאלה שמתאימה לסינון הזה. נסו נושא אחר או נקו את החיפוש." / "No question matches this filter. Try another subject or clear the search."
10. Error: "התשובה נשמרה, אבל הבדיקה לא הסתיימה. אפשר לנסות שוב." / "Your answer is saved, but the check did not finish. Try again."

## 8. Reviewer's checklist, per screen

- [ ] Fits 390 px with no horizontal scroll; touch targets ≥ 44 px; fits 1280 px without a sea of empty space.
- [ ] Right-to-left mirrors (logical properties; icons that point flip; the path zig-zag mirrors).
- [ ] Text contrast ≥ 4.5:1 (3:1 for ≥ 24 px and UI parts); focus visible; every icon button labelled.
- [ ] One primary action per screen, in the 3D button; secondary actions are text or outline.
- [ ] Copy is sentence case, concrete, in the coach's voice; both languages present; no tells from §7.
- [ ] Only one accent colour per component; no gradient text, glows, blobs, emoji.
- [ ] The motion budget (§4) is respected; reduced motion turns it off.
- [ ] Skill strength: five bars, long labels wrap on two lines, nothing overflows the card, RTL and LTR.
- [ ] Every class a component uses has a rule; nothing renders unstyled.
