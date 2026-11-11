---
version: 1
slug: "apps-web-src-app-tour-page-tsx"
primary_target: "apps/web/src/app/tour/page.tsx"
related_targets: ["apps/web/src/components/tour", "apps/web/src/lib/muxi-tour.ts", "apps/web/src/lib/member-tour.ts", "apps/web/src/components/personal-helper"]
---

# Muxi guided practice

The visitor preview shows what hardware and software interview practice feels like before signup. In the account, one optional walkthrough begins with the learner’s real goal. Keep both surfaces in the existing JobRun themes, with Hebrew and English, the site’s typefaces, controls and Muxi’s multiplexer silhouette.

Use a single start or resume action on the welcome screen. Inside the tour, show the current task, the control that performs it and the next step. Give the learner control over pausing, skipping or revisiting a station. Let Muxi react to input with finite gestures and a reduced-motion variant. The mobile layout must leave exercise controls accessible alongside navigation and guidance.

The public preview uses visibly identified samples, prewritten feedback and a prewritten interview report, with a direct signup action at the end. It does not save account practice. Preserve that existing journey.

The signed-in tour uses the actual account and bank, as requested on 2026-11-11. Its 12 stops cover the goal, personal area, interview library, explanation, code and live AI feedback, hardware/circuits, fundamentals and quizzes, games, friends, shop, mock interview and personal helper. Show the saved goal before editing. The explanation and code stops continue the same real attempt. An optional single-question game practice uses approved server-bank questions without creating a staked duel.

Regular saves, submitted answers, purchases and other explicitly chosen actions affect the account. Never perform those actions automatically to advance a tour. Keep microphone use, hints, reports, friend requests, purchases and timed-interview starts optional. Preserve drafts through the existing draft system. Keep the guide beside real controls, with responsive reserved space, collapsible guidance and accessible nested-dialog behavior. The personal helper starts closed and is available at its tour stop.

Verify guest and member journeys separately, including focus, dialogs, account-scoped checkpoints, real control/API wiring and mobile width. Use `verify-member.mjs` and `verify-member-games.mjs` for the current account flow. The older `verify-host.mjs` mixes retired sandbox assertions with useful dashboard regressions and must be preserved until those regressions are extracted.
