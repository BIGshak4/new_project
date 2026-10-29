# Quiz duels: implementation and rollout

29 October 2026. Game work is scoped independently from the parallel Mineral styling change.

## Entry points

- `/games`: authenticated live game lobby and match list.
- `/duel/<code>`: authenticated invite acceptance; joining always requires a deliberate button press.
- `/games/preview`: public, playable simulation with a labelled fake opponent, demonstration coins and draft content. It never calls the game API or changes an account.
- The practice home links to games in the header and below short fundamentals.

The game uses local CSS modules and existing semantic theme variables. Global colors, `mineral.css`, root layout and design-system documents are owned by the other chat. Only the root page's game links were added here.

## Match behavior

The server samples five distinct source IDs, then one variant per source, without reading player exposure history. Each linked source needs all five variants approved. The older standalone draft bank remains compatible but is not automatically approved. `docs/game-question-bank.md` records all 250 short sources and 1,250 bilingual variants, released for the pilot at Harel's explicit request on 29 October. The 40 standalone legacy drafts remain excluded.

Acceptance stakes both players' coins and opens a readiness lobby. The question stays hidden and the answering clock stays stopped until both players call `POST /v1/duels/{id}/ready`. Either participant can cancel before the clock starts. A lobby expires after ten minutes, with refunds processed on the next read. The active/null-deadline lobby fits the existing database schema; no new migration is required for readiness.

Both players receive the same five variants in the same order. Each has up to sixty seconds per question. Correct-answer count wins, then total answer time; a complete tie refunds both. The server controls timestamps, answers and coins. Snapshots of question text, choices, correct index, explanations and question duration are stored with the match so a later seed edit cannot change it. The browser sees correct options and explanations only in settled review rows. No AI call or XP/profile mutation occurs in quiz mode.

The UI polls while visible, resumes the selected match from its URL and refreshes on returning to the tab. Mutations are never automatically replayed. After a network failure, refresh status before retrying. The live client binds requests to the signed-in account and does not import the demo question bundle. The `readiness_required` capability flag prevents starting games against an older backend that starts clocks immediately on acceptance.

## Preview fixture

Run from `apps/web`:

```powershell
node tools/duels/sync-demo.mjs
node tools/duels/sync-demo.mjs --check
```

The exporter copies only the ten explicitly selected demo source groups, rather than publishing a future complete bank. These are public demonstration questions, not confidential test material. The answer-bearing JSON is imported only by the preview simulator; live clients receive their question from the API.

## Live activation still required

1. Harel explicitly authorized pilot publication of the completed 1,250-variant bank on 29 October. Content-bound release metadata preserves `professional_review: pending`; automated and AI checks do not assert expert human review.
2. Confirm that the existing coins and duels migrations have been approved and applied in the intended database. This implementation did not apply migrations or modify the live database.
3. Deploy the matching backend and frontend, then verify two real accounts: invite, both-ready, five answers, refresh/reconnect, settlement and wallet balances. This work's HTTP tests use authenticated test identities and an in-memory store; they do not prove the deployed database or provider configuration.

Payments are independent of game activation. No billing changes or automatic publication are part of this implementation.

## Verification on 29 October

- Backend offline suite: 1,656 passed, 11 skipped; the three live database suites were deliberately excluded. Includes two authenticated HTTP identities, readiness, snapshots, stale answers, authorization and coin race scenarios.
- Frontend existing plus simulator suite: 284 passed; four additional import-boundary tests passed afterward. The live route graph cannot reach the answer-bearing preview JSON or backend seeds; the preview graph reaches the demo dataset without the authenticated game API.
- Final TypeScript check and production build passed. Source/demo fixture synchronization and `git diff --check` passed.
- Browser: complete Hebrew demonstration match, correct settlement and wallet change, refresh/resume mid-match, English dark game, Mineral light, desktop and 390px mobile layouts. Header help opens the existing report dialog without covering answers or result controls. No physical phone or deployed two-account database test is claimed.
- Finish review resolved the two scored display defects (floating reporter overlap and reversed RTL ratios). See `docs/games-design-verification.md` for evidence and its scope.
