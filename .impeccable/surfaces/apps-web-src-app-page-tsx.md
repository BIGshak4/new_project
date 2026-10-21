---
version: 1
slug: "apps-web-src-app-page-tsx"
primary_target: "apps/web/src/app/page.tsx"
related_targets: ["apps/web/src/components", "apps/web/src/app/ion.css"]
---

# JobRun production Ion

Mode: Operate for the authenticated app; Persuade for its public sign-in landing.
On 2026-10-01 the user explicitly approved the adaptive Ion simulation and requested production integration, dark by default, with a light toggle and full verification. The working preview at `/site-preview?style=ion-adaptive` is the visual authority, superseding Workbench on the practice site. Tasks are outside this change. On 2026-10-02 the user changed the first-visit default to light; explicit saved theme choices still persist.

## Direction contract
THESIS: A confident engineering learning environment, with room to reason and a clear next step.
OWN-WORLD: Ion's violet midnight, lilac text accents and amber actions; its alternate cream canvas and deep purple type. Heebo 400/500/700/900, JetBrains Mono for code; 7px controls, 12px panels, thin dividers. No graph paper, handwriting, navy header or sticky-note metaphor.
STORY: Sign in, set a real goal, follow the program, answer with text/code/circuits/photos, use hints, receive genuine backend feedback, revisit progress and practice interviews. Never substitute the simulation's sample records for production data.
FIRST VIEWPORT: Spacious paired landing headline and the approved physical violet chip; interactive XOR switches. Authenticated header has four destinations, compact theme/language tools. Work pages retain functional backend flows under the preview's quieter shell, typography and split panes. Mobile stacks panes and uses bottom navigation.
FORM: Inherited user-selected Ion direction (seed lineage 9e6466ae, docs/ten-independent-design-worlds.md); no new random direction. Exact approved reference screenshots are `.impeccable/review/full-site/ion-desktop.png`, `ion-light-desktop.png`, `adaptive-practice-dark-desktop.png`, `adaptive-practice-light-desktop.png`, `circuit-dark-desktop.png` and matching mobile captures. Production evidence is under `.impeccable/review/ion-production/`.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Quality bar
Readable Hebrew RTL and English LTR, keyboard focus and touch targets in both themes, durable optional theme storage with light default and no first-paint flash. Theme changes must not remount editors or reset attempts. Questions, solutions, diagrams and metadata remain intact. Existing raster `/design-worlds/ion-chip.png` retains its embedded prompt and provenance.json. Backend and database permissions remain unchanged.

## Technical notation correction, 2026-10-18

The user supplied a broken rendering of `example-enabled-decoder`: the source has correct `Y[3:0]` and `A[1:0]` but their closing brackets escaped the old LTR isolates. Preserve the approved Ion design and fix shared rendering across questions, references, hints, feedback, interview reports, metadata and tours in both languages. Keep complete technical units and their brackets together, including nested expressions, intervals and Markdown formatting boundaries. Derive each prose block's direction from its original content before isolation. Code and deliberately invalid bracket examples must retain their exact source characters and visual order; ordinary Hebrew parentheticals retain their RTL reading order. Do not rewrite the bank or affect editor drafts, account data or assessments. Verify the complete bilingual catalog and independent glyph-position cases at desktop and phone sizes in both themes, plus the real app decoder screen.

## Quick fundamentals extension, 2026-10-21

The authenticated library gains a fundamentals subview, also reachable from Today. It contains 200 original bilingual short exercises in a single-question reading flow, with topic filtering, search, explicit answer reveal and completion/skip/surprise navigation. The catalog contains 100 hardware, 70 reasoning and 30 code/algorithm cards. Both the interview library and fundamentals get a fresh shuffled order on entry; filtering, language changes and background history refresh preserve that visit's order. Existing interview questions retain their own bank and assessment workflow. The original 120 short-card IDs, contents and revision hashes remain unchanged.

The extension preserves Adaptive Ion. It uses an 860px reading column, the incumbent flat sheet and semantic colors, readable Hebrew/English text, and native SVG gate/FSM diagrams with explicit LTR technical labels and arrowheads. On phones (600px and below), topic/search controls start collapsed behind a labelled toggle, library subnavigation wraps into two columns, and action labels wrap within 44px minimum touch targets. Revealing an answer leaves its control in place. Navigation and confirmed saves reset the answer and focus the rendered question or empty-state heading after commit; write errors also restore heading focus.

Completion is explicitly self-reported and saved per signed-in user through the authenticated backend and `supabase/migrations/20261021132032_fundamentals_completion.sql`. Opening an answer and skipping do not complete a question. The default unfinished view omits recorded completions; finished and all views support revisiting them, showing a written completion status and date. An undo action marks a question unfinished. Known content updates preserve previous completion in history with an updated label, rather than silently returning it to unfinished. None of this awards XP or assesses correctness.

Initial history read gates question display; a failed read offers retry before continuation. Background refresh preserves the current question and loaded history, warning on failure without replacing the practice flow. Save failure does not advance or mark completion; retry remains available on the same question. Successful retry and write-error recovery focus the rendered heading. Review labels distinguish frozen existing solution attestations from new exercises awaiting human review, independently of difficulty calibration and automated feedback.

Current 200-card rendering evidence is `.impeccable/review/quick-200-20261021/desktop-200.png` and `mobile-fsm-solution.png`. The full local app with a memory backend verified shuffled library order, language/search stability and persistent completion across a page reload. Phone-width evidence uses the real component in a 390px frame. Earlier history evidence remains `.impeccable/review/quick-progress-20261021/mobile-history.png`. Captures use synthetic local test accounts, not an authenticated production click-through or a physical phone. No new raster assets or visual world were introduced.
