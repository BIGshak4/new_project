# Muxi guided tours

Implemented on 2026-10-18. Muxi (מוקסי) is the temporary name for the site's multiplexer guide.

## What users get

- A recommended **full tour with 46 hands-on stations**, arranged in replayable chapters.
- A **short tour with 9 hands-on stations** covering the four main product areas and the essential learning tools.
- A cute, authored SVG multiplexer with eyes, short arms and legs, pointing and completion poses. Motion is finite and respects reduced-motion preferences. It points toward the exercise on desktop and downward on stacked phone layouts; the relevant control is highlighted.
- An explicit route choice, per-station skip, previous station, chapter navigation, pause/resume, and clearly labelled exit controls. Completing an interaction unlocks Continue; skipping is a separate action.
- A permanent **Tour with Muxi** button in the authenticated workspace and a public introduction at `/tour`, also linked before sign-in.
- A one-time offer on the first authenticated visit to this tour version on the current device. Existing users can replay it at any time.

The comprehensive tour covers goals, library search and company aliases, topic filters and original examples across the current topic families, explanation/code entry, code languages/completion, circuit wiring/components/configuration, simulation and truth tables, undo/export/expanded workspaces, MUX selection, sequential clock/reset, graduated hints and reference exposure, diagrams/downloads, image selection/removal, example feedback and follow-ups, confidence/reporting, interviews/reports, bookmarks/history, skills/readiness/plans, theme and language. An analog example is explicitly marked as a future topic rather than an active learning-track promise.

## Real tools, isolated examples

The tour reuses the production `AnswerEditor`, `CircuitEditor` and integrated `CircuitTruthTable`. CodeMirror editing/completion and the local circuit simulation engine are real. Original bilingual sample questions and local examples demonstrate workflows that would otherwise mutate user data.

Tour feedback is fixed instructional content, clearly labelled as a sample. It is **not** an AI evaluation of the learner's typed answer. The tour does not call a model, create real attempts, earn XP, consume practice quotas, upload to Supabase, or change a real goal/program. Image previews use the same local preparation function as real answers, including image validation and metadata removal; tour images remain local and their object URLs are cleaned up.

Theme/language buttons change the genuine product preferences. Dictation remains an optional explicit user action in the real answer editor; no microphone permission is requested automatically.

The live workspace stays mounted and becomes inert while the tour is open. The tour never navigates it or resets its editor/draft state. A shared reference-counted body scroll lock supports either nested-dialog cleanup order. Expanded circuit dialogs render their own coach slot in the browser's top layer, rather than trying to out-rank a native dialog using z-index. The phone coach starts minimized, with labelled restore and exit controls, and can be minimized again to use the canvas.

## Progress and storage

`jobrun-muxi-tour-v1-<user ID>` stores only versioned station IDs, route choice, completed/skipped stations, status and an update timestamp. Anonymous visitors use a separate visitor key. Answers, code, circuits, image data, authentication tokens and personal profile fields never enter this record.

Storage is optional. Corrupt/unsupported/oversized records reset safely; foreign station IDs and duplicate marks are removed. Completion takes precedence over a skip. The offer and pause/resume state are device-local, not synchronized across browsers/devices. Demo exercise content stays in memory; the persistent checkpoint preserves the place in the tour, not all example drafts.

No schema migration, database credentials, backend routes or model configuration changes are needed.

## Main implementation boundaries

- `apps/web/src/lib/muxi-tour.ts`: bilingual station catalog, action requirements and bounded progress parsing/checkpoint logic.
- `apps/web/src/components/tour/muxi-tour.tsx`: chooser, launcher, coach, highlighting, action gating, focus and pause/replay behavior.
- `apps/web/src/components/tour/tour-exercises.tsx`: local examples and reused production editors.
- `apps/web/src/components/tour/muxi-mascot.tsx`: native SVG mascot and poses.
- `apps/web/src/app/tour/page.tsx`: anonymous public entry point.
- `apps/web/src/lib/body-scroll-lock.ts`: nested scroll locking shared with the circuit editor.
- Optional `CircuitEditor.onActivity`, `CircuitEditor.guide` and `CircuitTruthTable.onGenerate` props expose local tutorial events without changing circuit serialization or normal practice behavior.

Actions are scoped to the current station. An action from one station cannot accidentally complete the next. Successful interaction is separate from technical correctness: editing code unlocks the editor station, but does not assert the code is a correct answer.

## Verification

Release checks passed: **213 frontend tests**, the production build, **198 full browser-suite checks**, **41 focused mobile-coach checks**, and **12 authenticated integration checks**. Both tours were completed without skipping their required interactions. The final targeted review scored the mobile coach obstruction fix resolved; the ordinary-extension documentation preserved the incumbent design system. Local evidence is in `.impeccable/review/muxi/` (ignored from Git), including `e2e-final/report.json`, `e2e-final/report-mobile-supplement.json` and `host-report.json`.

The frontend unit suite includes progress/schema/action-gating and nested scroll-lock regression tests. Browser verification traverses the complete full and short tours with real controls and no station skips. It also exercises language/theme changes, CodeMirror completion and keyboard exit, accessible wiring, truth-table contents, simulation/clock/reset, native expanded coaching, image rejection/selection/removal, local feedback and interviews, chapter navigation, backtracking, exit/replay/resume, and blocked/corrupt browser storage. Phone checks use 390×844 and desktop checks use 1440×1000.

Authenticated integration is tested with the existing in-memory screenshot-server API/auth fixture. Browser requests are intercepted to that local fixture, with unexpected external requests blocked. Checks include first offer, no repeated offer after reload, permanent replay, covered-workspace inertness, preserved real library state and unsent practice text, nested dialog removal/scroll restoration, and a visible mobile launcher.

Reusable verification commands (run from `apps/web`):

```powershell
npm test
npm run build
node tools/tours/verify.mjs http://localhost:3212 C:/path/to/local-output
node tools/tours/verify-host.mjs http://localhost:3212 C:/path/to/screenshot-session.json
```

The scripts use a fresh owned headless Edge context, not a user's browser profile. The public-tour verifier supports `PLAYWRIGHT_MODULE` and `EDGE_EXECUTABLE`. The host verifier supports `PLAYWRIGHT_PACKAGE_ROOT` (a package.json used for Node resolution) and `EDGE_PATH`. Point these at an installed/bundled Playwright and browser on another machine. A local screenshot-server session is required only for authenticated integration, never a real user's password or production service-role key.

The fixture feedback does not establish real-model quality. No live personal answers, real uploads, or paid-model evaluations are part of tour verification.
