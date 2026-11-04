# Personal helper handoff

Recorded 2026-11-04 after finish-review disposition: ship, no fixes. This is an ordinary extension of Mineral light / Ion dark. `DESIGN.md`, `.impeccable/design.json` and `PRODUCT.md` remain the incumbent authorities and were not modified by this documentation pass.

## Integration and scope

`apps/web/src/app/layout.tsx` mounts `PersonalHelper`. Its implementation is in `apps/web/src/components/personal-helper/`; authored bilingual content, destinations and focus targets live in `apps/web/src/lib/personal-helper.ts`.

The helper appears on `/`, `/games`, `/games/shop`, paths beginning `/games/preview`, and `/duel/`. It is absent elsewhere. The inline-end avatar launcher opens a nonmodal conversation panel; Escape or minimize closes it and restores launcher focus. Back removes the last turn; All topics resets the conversation. Minimize retains the history. History is component memory in the current tab, not saved conversation storage; reload, leaving the mounted route scope, or changing account/demo context can reset it.

The helper starts minimized on every fresh visit or reload and opens only when its launcher is pressed. It never restores an open state from browser storage.

The user's follow-up explicitly removes the character shortcut from the shared top navigation. Personal character customization remains accessible through the shop and the helper, and in-game avatars remain intact. Identity, friends and clothing changes from the concurrent task are preserved. Existing character rendering and save notifications are integration dependencies, not a redesign of those areas.

## Authored topics and actions

The five starting choices cover finding one's way around, practice tools, contacting the team, character/games, and useful shortcuts. Subtopics explain the library, personal area, tour, mock interviews, freeform reasoning, dictation, software editing/execution, hardware construction/checking, hints and feedback, and support categories.

This is a guided menu with authored Hebrew and English responses, not AI chat. It does not read, grade, execute or submit a user's answer. Focus actions locate visible, enabled explanation, code, run, circuit or feedback controls. If unavailable, a written notice offers the tour. Navigation uses fixed local destinations and labelled new-tab links, preserving mounted practice in the original tab. Preview game/shop destinations stay in preview. The existing Muxi tour opens in place; support and inbox actions open their existing interfaces.

## Avatar and support safeguards

`use-helper-avatar.ts` reuses `LogicAvatar`, loads the signed-in user's saved configuration or demo avatar, and falls back to the default character. `avatar-events.ts` validates `jobrun:avatar-updated` payloads against account and demo scope. Successful API mutations and demo saves publish updates; the refresh guard prevents older reads from overwriting a newer save. Window focus/visibility refreshes the avatar; account changes cannot briefly expose the previous owner's outfit. A failed refresh retains an already loaded avatar.

`openSupportReport(category)` dispatches the existing support event with a validated category: bug, question, feedback or other. `support-reporter.tsx` applies the category only to a fresh draft. Subject, description, attachments, an explicitly edited category, uploads, report IDs, retry/error or submitted state count as an existing draft and preserve its details/category. A written notice explains preservation when the requested category differs. Closing the modal retains its draft in the tab; submission remains a separate user action and the existing guest/auth gate remains in force. The helper minimizes before opening the modal and hides while native dialogs or the tour are active.

## Visual continuity

The surface inherits `--surface`, `--ink`, `--ink-2`, `--muted`, `--line`, `--link`, `--soft` and `--font`: Mineral's cool gray-green/plum palette and dark Ion's violet/lilac palette. There is no new font or raster asset. Helper headings use Heebo at 18px (17px mobile) and 19px; response text is 14px with 1.8 line-height, with 11–13px supporting text. Logical alignment and explicit Hebrew/English direction follow the incumbent Direction-Aware Text Rule.

The 390px panel uses 12px corners, fine dividers, open text-choice rows and a scrolling body. Below 780px it fits within 12px side insets above the 72px tab bar and safe area. Controls retain at least 44px targets, with 49px choice rows and visible keyboard focus. Its 180ms, 8px entrance and choice transitions are disabled for reduced motion. Theme Continuity and Labelled State remain applicable. Local floating-overlay shadows are descriptive of this helper only, not new structural-shadow rules for working sheets.

Pre-existing drift not canonized or repaired: `DESIGN.md` describes the landing chip field as bordered with a surface fill, while current `mineral.css` sets `.ion-art` to `border: 0` and transparent background. This is outside the helper scope. Previously recorded dormant Workbench selectors and incomplete task sidecar snippets also remain outside this pass.

## Verification and limits

Implementation handoff reports 32 scoped tests passing, TypeScript checking passing, and a successful webpack production build. These checks were not rerun for this documentation-only addition. Browser/demo verification covered history/back/minimize, theme/language, missing-control fallback, tour, support guest gate and demo avatar save. It did not perform a real authenticated support submission.

Reviewed evidence in `.impeccable/review/personal-helper-20261104/`: `brief.md`, `desktop-light.jpg` (1280px viewport), `mobile-light-support.jpg`, `mobile-dark-english.jpg` (390px viewport), and `mobile-320.jpg` (narrow overflow check). These are local browser/demo evidence, not production-account or physical-device validation.
