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
FIRST VIEWPORT: Spacious paired landing headline and the approved physical violet chip; interactive XOR switches. Authenticated header has three destinations: Personal area, Library and Mock interview, with compact theme/language tools. Work pages retain functional backend flows under the preview's quieter shell, typography and split panes. Mobile stacks panes and uses bottom navigation.
FORM: Inherited user-selected Ion direction (seed lineage 9e6466ae, docs/ten-independent-design-worlds.md); no new random direction. Exact approved reference screenshots are `.impeccable/review/full-site/ion-desktop.png`, `ion-light-desktop.png`, `adaptive-practice-dark-desktop.png`, `adaptive-practice-light-desktop.png`, `circuit-dark-desktop.png` and matching mobile captures. Production evidence is under `.impeccable/review/ion-production/`.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Quality bar
Readable Hebrew RTL and English LTR, keyboard focus and touch targets in both themes, durable optional theme storage with light default and no first-paint flash. Theme changes must not remount editors or reset attempts. Questions, solutions, diagrams and metadata remain intact. Existing raster `/design-worlds/ion-chip.png` retains its embedded prompt and provenance.json. Backend and database permissions remain unchanged.

## Navigation simplification, 2026-11-03

At the user's request, Today is now Personal area (אזור אישי), and the separate Progress category and its dedicated overview, readiness and plan-table screens are removed. The authenticated desktop and phone navigation, public previews and Muxi tours follow the same structure. Old Progress links resolve to Personal area while preserving a linked attempt or question. Daily practice, goals, skills, streaks and saved history continue to use the existing account data.

## Goal setup, 2026-11-03

Fresh workspace visits enter Personal area, including saved category URLs; direct links to a question, attempt or ongoing interview retain their work. In-session navigation remains available.

Goal setup uses four initially closed disclosure bars in this order: roles, daily time, career stage, interview date. Multiple selected roles remain visible as removable cards with the catalog's descriptions. Daily time offers presets and a whole-minute value from 5 to 600. A native date field is optional through an explicit no-interview-date choice. The alternative “I don't have a defined goal. Teach me” approach displays every role description and keeps the same time and career controls without an interview date.

The complete role selection and learning approach persist in the existing profile and drive real combined-role or broad-learning plans. The interface retains drafts on language changes and save failures, opens invalid collapsed fields, and uses native keyboard controls. Verification used the actual frontend and an isolated memory-backed API at 1360px and 390px in Hebrew light and English dark, including save/reopen, custom minutes, optional date, role selection, broad-learning program generation and Personal area on reload. No new visual world, account entitlement or image asset is introduced.

## Personal recommendations, activity and discovery, 2026-11-03

Personal area adds a curved path of up to three exact next-question recommendations from the authenticated backend. Each node names its real question, focus and rationale and opens that question. The path uses horizontal waves on desktop and a vertical curve on phones; daily program and work-ahead rules remain intact. The internal focus-skill card stays absent.

The header shows canonical wallet balance and consecutive local days with at least one assessed main answer, including answered turns in completed interviews. XP, level labels and positive-XP-only streak logic do not drive the header. Opening the streak shows its rule and recent dates/counts, with honest zero, loading and retry states. Activity is account-scoped; the device's IANA timezone determines calendar days. Self-report checkboxes, mere visits, skipped turns and demonstration evaluations do not count.

The public sign-in tour offers only the short Muxi introduction, including legacy resume and completion; authenticated tour choices retain their existing scope. Library filters start empty at every new workspace visit and refresh, independently of the saved learning goal. Status, discipline, topic, role and company selectors allow multiple checked values. Choices within one selector form a union; selectors and free-text search intersect. Empty choices show all questions, including personal hidden/completed flags; those flags themselves remain saved. Hebrew and English company aliases remain searchable.

## Persistent goal and library navigation, 2026-11-03

The saved learning goal appears first in Personal area's main column, above the daily headline and practice. Its flat Ion sheet displays the selected roles or broad-learning approach, daily minutes, career stage and optional interview date. One explicit Edit goal action opens the full existing disclosure editor immediately below the summary. Saving returns focus to the updated summary at the page start and refreshes the real plan and question recommendations. Automatic scrolling to daily practice no longer hides these preferences on entry.

Library subnavigation contains Interview questions, A little practice and Saved. My practice is absent from navigation; saved attempts, drafts and existing direct report links retain their data and route support. Tour and practice copy follows the simplified navigation.

Verification used the actual frontend with an isolated memory-backed backend at 1360px and 390px, Hebrew light and English dark. It covered an account with an assessed answer, initial summary visibility, all editor controls, multi-role changes, custom minutes, career/date changes, saved program updates, reload persistence, broad learning, three library tabs and a saved-attempt link. All 345 frontend tests and the production build passed. No visual world or raster asset changed.

## Technical notation correction, 2026-10-18

The user supplied a broken rendering of `example-enabled-decoder`: the source has correct `Y[3:0]` and `A[1:0]` but their closing brackets escaped the old LTR isolates. Preserve the approved Ion design and fix shared rendering across questions, references, hints, feedback, interview reports, metadata and tours in both languages. Keep complete technical units and their brackets together, including nested expressions, intervals and Markdown formatting boundaries. Derive each prose block's direction from its original content before isolation. Code and deliberately invalid bracket examples must retain their exact source characters and visual order; ordinary Hebrew parentheticals retain their RTL reading order. Do not rewrite the bank or affect editor drafts, account data or assessments. Verify the complete bilingual catalog and independent glyph-position cases at desktop and phone sizes in both themes, plus the real app decoder screen.

## Quick fundamentals extension, 2026-10-21

The authenticated library gains a fundamentals subview, also reachable from Today. It contains 200 original bilingual short exercises in a single-question reading flow, with topic filtering, search, explicit answer reveal and completion/skip/surprise navigation. The catalog contains 100 hardware, 70 reasoning and 30 code/algorithm cards. Both the interview library and fundamentals get a fresh shuffled order on entry; filtering, language changes and background history refresh preserve that visit's order. Existing interview questions retain their own bank and assessment workflow. The original 120 short-card IDs, contents and revision hashes remain unchanged.

The extension preserves Adaptive Ion. It uses an 860px reading column, the incumbent flat sheet and semantic colors, readable Hebrew/English text, and native SVG gate/FSM diagrams with explicit LTR technical labels and arrowheads. On phones (600px and below), topic/search controls start collapsed behind a labelled toggle, library subnavigation wraps into two columns, and action labels wrap within 44px minimum touch targets. Revealing an answer leaves its control in place. Navigation and confirmed saves reset the answer and focus the rendered question or empty-state heading after commit; write errors also restore heading focus.

Completion is explicitly self-reported and saved per signed-in user through the authenticated backend and `supabase/migrations/20261021132032_fundamentals_completion.sql`. Opening an answer and skipping do not complete a question. The default unfinished view omits recorded completions; finished and all views support revisiting them, showing a written completion status and date. An undo action marks a question unfinished. Known content updates preserve previous completion in history with an updated label, rather than silently returning it to unfinished. None of this awards XP or assesses correctness.

Initial history read gates question display; a failed read offers retry before continuation. Background refresh preserves the current question and loaded history, warning on failure without replacing the practice flow. Save failure does not advance or mark completion; retry remains available on the same question. Successful retry and write-error recovery focus the rendered heading. Review labels distinguish frozen existing solution attestations from new exercises awaiting human review, independently of difficulty calibration and automated feedback.

Current 200-card rendering evidence is `.impeccable/review/quick-200-20261021/desktop-200.png` and `mobile-fsm-solution.png`. The full local app with a memory backend verified shuffled library order, language/search stability and persistent completion across a page reload. Phone-width evidence uses the real component in a 390px frame. Earlier history evidence remains `.impeccable/review/quick-progress-20261021/mobile-history.png`. Captures use synthetic local test accounts, not an authenticated production click-through or a physical phone. No new raster assets or visual world were introduced.
