# Muxi guided tours

The public route `/tour` lets visitors try JobRun before signup. The signed-in **Tour with Muxi** launcher opens a single account walkthrough. Both work in Hebrew and English, including on phones. The tour stays optional on account entry.

The visitor explores an interview question and a short fundamentals question, completes a three-sensor alarm in the circuit editor, and generates its truth table. Two consecutive software stops use the same array maximum question. The visitor submits a written explanation, reads feedback prepared for the sample, then checks a repair in the code editor. A one-question written interview ends with an explicitly prewritten report. The personal helper appears only after sign-in. Visitors can skip stations, pause and return, or follow the link to signup.

## Signed-in walkthrough

As of 2026-11-11, the member tour accompanies the actual account UI. It replaces the former goal-save-only walkthrough and its sample exercises. The public preview described above is unchanged. One optional `MemberTour` controller in the app layout guides 12 stops, with Hebrew and English copy in `src/lib/member-tour.ts`.

| Stop | Actual surface and interaction |
| --- | --- |
| Goal | Keep a saved goal or use the real role, daily-time, career-stage and interview-date form. Only an explicit save updates the plan. |
| Personal area | Understand recommended question waves, the daily plan, resume an unanswered question, and find the saved goal and profile. |
| Interview library | Search, open a question, and locate the grouped issue, unclear-question and company-report actions. |
| Explanation | Open a real software-bank question, start practice and write an explanation. Dictation and hints remain optional. |
| Code and feedback | Continue the same attempt with the real code editor and execution controls. Explicit submission uses the regular AI feedback flow and saves the answer. |
| Hardware | Open a real hardware-bank question and use the circuit editor, component settings, connections, input values, truth table, clocked simulation when applicable, and attachments. |
| Fundamentals | Use the actual short-question bank, completion controls and topic picker for a ten-question self-study quiz. |
| Games | Fetch an approved multiple-choice bank question and check the selected answer on the server. This single-question practice creates no duel and changes no coins, XP or mastery. |
| Friends | Locate the personal friend code, request form and real duel invitation control. Sending a request or creating a duel is optional. |
| Shop | Try actual skins, inspect prices, and find component/color and save controls. Purchases and saved outfits require explicit user actions. |
| Mock interview | Choose a duration and locate the actual answer tools, final report and interview history. Starting a timed interview is optional. |
| Personal helper | Open the user's avatar helper and choose a guidance topic. Its updated content covers current site features and shortcuts. |

The guide highlights visible live controls without making the workspace inert. It reserves space on desktop, can collapse on phones, and follows native dialogs into their top layer. It never starts a microphone, submits an answer, reveals a hint, sends a report or friend request, buys a skin, or starts an interview on the learner's behalf. Optional tasks and whole stops can be skipped, paused and revisited. Regular account effects apply to actions the learner chooses to perform. Answer drafts continue to use the existing draft recovery system, including across route changes.

Submitting a primary answer marks its question `completed` as soon as the server accepts it, independently of the eventual grade. Real feedback appears when the ordinary assessment finishes. A scripted or pending assessment must not satisfy the tour's real-feedback milestone. The signed-in tour contains no prewritten AI assessment. Opening a short-question solution or the self-study quiz does not imply completion or an AI grade.

The games practice uses authenticated `GET /v1/duels/practice` and `POST /v1/duels/practice/answer`. The server selects approved bank content, withholds the correct answer until checking, and binds an expiring signed round token to the account and question version. Errors and expired rounds provide retry/new-question paths. The existing staked multiplayer duel remains a separate explicit action.

## State and integration

- `MEMBER_TOUR_START_EVENT` opens the guide for its `{ userId }` owner. Header and helper launchers use the same controller.
- `MEMBER_TOUR_NAVIGATE_EVENT` requests a real workspace `{ userId, route }` navigation. Cross-page moves persist the checkpoint before navigating.
- `MEMBER_TOUR_ACTION_EVENT` carries `{ userId, action }` for successful goal saves, ready feedback and helper use. The controller also observes rendered real results and visible control interactions.
- `jobrun:member-tour-practice` records the selected question/attempt context so explanation and code use the same attempt.
- `localStorage` key `jobrun-member-tour-live-v1-${userId}` contains only progress, skipped stops and timestamps, with `paused`, `active` or `completed` status. Session keys ending in `:active` and `:questions` retain the current tab's active state and question/attempt identifiers. They do not contain answer text, source code, credentials or model responses.
- The public `muxi-tour` checkpoint remains separate. Old short/full and member sample checkpoints do not become live-tour progress. Storage failures do not disable the guide, though checkpoint recovery is then unavailable.
- The personal helper is authenticated-only and starts closed. It is hidden during the tour except at the helper stop, and remains hidden behind native modal dialogs. Its avatar continues to track the saved account outfit.

Muxi's finite gestures and text remain usable with reduced motion. The public preview still uses clearly identified local samples and never saves practice or purchases to an account.

## Verification

From `apps/web`, use these commands with a local web server and the existing screenshot-server fixture:

```powershell
npm test
node tools/tours/verify.mjs http://localhost:3291 C:/path/to/preview-output
node tools/tours/verify-member.mjs http://localhost:3291 C:/path/to/fixture-session.json
node tools/tours/verify-member-games.mjs http://localhost:3291 C:/path/to/fixture-session.json
```

The guest verifier traverses the preview on desktop and phone, checks sample interactions, resume and the signup destination, and checks for unexpected account or model requests. The member verifiers use a local screenshot-server fixture and intercept authenticated requests before they can reach production. They exercise actual UI/API wiring, persisted goal and practice behavior, game-bank checking, helper interaction, route recovery, and responsive layouts. A fixture assessment verifies the integration contract, not production model quality. Use `PLAYWRIGHT_MODULE` / `EDGE_EXECUTABLE` for the guest verifier and `PLAYWRIGHT_PACKAGE_ROOT` / `EDGE_PATH` for the member verifiers.

`verify-host.mjs` targets the retired member sandbox and is not the acceptance test for the live-account tour. It also contains useful dashboard, draft and automatic-completion regressions. Preserve those checks until extracted into a compatible standalone verifier; do not remove them merely because the old tour assertions no longer apply.
