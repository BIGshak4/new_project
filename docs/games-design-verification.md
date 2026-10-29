# Games design verification

29 October 2026. Ordinary extension of the existing JobRun practice system. This note records the shipped local implementation and its evidence boundaries; it does not establish a new visual world or replace the shared design registry.

## Inherited system

The direction contract in `.impeccable/surfaces/apps-web-src-app-games-page-tsx.md` calls for a focused five-question competition, Hebrew-first logical spacing, shared semantic colors and restrained panels. The implementation uses these inherited rules without a second palette:

- **Palette:** `paper`, `surface`, `surface-2`, `ink`, `muted`, `line`, `link`, `action` and `action-ink` resolve from the root theme. The parallel, user-approved Mineral light work supplies the current gray-green grounds, plum text and purple actions through `mineral.css`; existing dark Ion supplies violet grounds, lilac emphasis and amber actions. Correctness and errors use the existing `ok`/`ok-soft` and `danger`/`danger-soft` roles, accompanied by text.
- **Type:** the shell inherits the loaded Heebo variable with system-ui/sans-serif fallbacks. The local introductory heading is fluid (30–46px, weight 900); question text is 24–32px, weight 700, line-height 1.65; choices are 17px, then 16px on narrow screens. Supporting labels use 12–15px. Numbers use tabular figures. These are observed surface choices rather than additions to the global type ramp.
- **Theme Continuity Rule:** local fills, outlines, feedback and text use semantic variables. The existing theme and language controls are reused. Theme changes do not introduce another game-specific color definition.
- **Direction-Aware Text Rule:** logical borders, spacing and alignment support Hebrew/English. Prompts and review content have their own language/direction; technical text passes through `BidiText`. Invite fields and score fractions explicitly use LTR direction; coin deltas are isolated with `bdi`.
- **Quiet Depth and Labelled State Rules:** fine borders and tonal separation define panels without structural shadows. Written ready, correctness, unavailable and result messages retain meaning alongside icons and colors. No shipping raster asset was added.

## Local composition and controls

Source: `apps/web/src/components/duels/duels.module.css` and `duel-workspace.tsx`. The games page uses a 980px maximum content area at 90% width, with a 780px play column. The header has an 84px minimum height. The creation/join area uses two columns and open dividers; history uses divided rows. Lobby, waiting, question and result surfaces use inherited fill/border roles with 12px corners. Controls use 7px corners and choice markers use 5px corners.

At 650px and below, the header becomes 73px, the main area becomes 92% wide, creation/join and invitation controls stack, question padding becomes 20px 18px, and bottom padding accounts for the safe area. Choices remain full width, at least 62px high (66px on wider screens). General controls retain a 44px minimum target. Links, buttons and inputs have a 2px link-colored keyboard outline with a 4px offset. New questions receive programmatic heading focus; the countdown does not announce every tick. The timer track uses a 250ms linear transform transition, disabled for reduced motion.

The local primary button has a 44px minimum and brightness(1.08) hover, while the incumbent system describes 46px and brightness(1.06). Question padding, local breakpoints and surface heading sizes also differ from the generic practice-sheet examples. These implementation differences are recorded here without promoting them into shared tokens or repairing them outside this extension's scope.

The scored review fixes place the support reporter action in the compact header and suppress its floating sibling in this shell, retaining an explicit accessible action without covering answers. Score fractions and signed coin deltas now preserve their intended order in RTL.

## Entry points and data boundaries

`/games` and `/duel/[code]` render the authenticated `DuelPage`; `duel-page.tsx` creates the account-bound live API client. `/games/preview` renders `DuelPreview` with the separate simulator and an explicit preview notice, simulated opponent, demonstration coins and draft-content disclosure. The answer-bearing fixture is imported only by the preview path; the live client receives match data from the API. Rendering the shared workspace with the simulator does not verify the live service.

The visible sequence is invite/accept, both-ready lobby, five timed questions, waiting, result and answer review. The server controls the live clock, correctness and coin settlement; the preview imitates the flow locally. URL selection supports resuming a match. Polling while visible and refresh on tab return obtain current status; uncertain writes show a refresh-before-retry message. Games explicitly state that they do not change XP or skill profiles. Content review and rollout details remain in `docs/games-integration.md` and `docs/game-question-bank.md`.

## Evidence and limits

Local rendering captures in `.impeccable/review/games/`:

| Capture | Evidence |
| --- | --- |
| `desktop-question-light.png` | Current Mineral light question surface and corrected RTL score fraction. |
| `desktop-home.png` | English dark games home. |
| `desktop-lobby.png` | Hebrew lobby; historical earlier light palette, not authority for current Mineral values. |
| `desktop-question-dark.png` | Dark question rendering. |
| `mobile-question.png`, `mobile-answers.png` | Narrow question/answer layout and scored reporter placement fix. |
| `mobile-result.png`, `mobile-review.png` | Narrow result, signed demonstration coin change and answer review. |

This documentation pass directly inspected `desktop-question-light.png` and `mobile-result.png` alongside the source; the remaining captures and interaction results were supplied by the parent implementation/review pass. That pass played a full Hebrew preview to 5/5 and +5 demonstration coins, refreshed during question two and resumed at question three, and checked English dark rendering and a new game. These are local simulated flows, not two-account production evidence or physical-phone validation.

The finish reviewer returned **ship** for the two scored findings: reporter overlap and RTL score ordering were resolved, with no visible regression in that reviewed batch. This disposition is limited to those fixes; it is not general production approval. No live migrations or deployment occurred. Fifty new bilingual variants remain drafts pending human review; automated checks do not attest review.

## Preserved authority and uncanonized drift

Checked `PRODUCT.md`, `DESIGN.md`, `.impeccable/design.json`, the games surface contract, `mineral.css`, the applicable Ion tokens, the games stylesheet, workspace, live/preview wrappers and route entry points. Preserved `DESIGN.md`, `PRODUCT.md`, `.impeccable/design.json`, root layout, all global styles and all source files; this pass writes only this note. The ordinary extension does not require a registry or sidecar regeneration, and the parallel chat retains ownership of the Mineral system.

Not canonized or repaired: local control/hover and composition differences above, plus the incumbent document's already-recorded dormant Workbench selectors, incomplete task sidecar snippets and unsampled drift. They remain outside this scoped verification; no defect or task-specific device is promoted into a house rule.
