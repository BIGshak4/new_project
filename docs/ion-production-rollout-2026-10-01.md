# Production Ion rollout — 1 October 2026

## What changed

Harel selected the adaptive Ion simulation as the production practice site's visual direction: violet midnight by default, with a cream/deep-purple light mode. This release applies that direction to the real application at https://jobrun-practice.netlify.app, rather than replacing the application with the demonstration screens.

- The compact sun/moon button sits beside the language control, before and after sign-in.
- A first visit starts dark, irrespective of the operating-system preference. An explicit light choice is remembered in `jobrun-theme` on that browser. A small pre-paint script restores the choice; blocked storage does not prevent theme switching during the visit.
- Theme changes update CSS variables in place. They do not recreate the workspace, code editor, circuit editor, drafts, attempts or API client. Other tabs follow changes to the stored preference.
- The public landing reuses the approved violet chip and its interactive XOR inputs. Its sign-in form still uses the existing authentication and pilot-membership checks.
- The actual question library, goal and daily plan, practice, hints, reference solutions, feedback, mock interviews and progress screens use the Ion palette and typography. Code syntax, charts, circuit pins/wires, menus, notifications and mobile navigation also adapt.
- The old graph-paper, handwriting and heavy navy treatment were removed from the practice site's presentation. Design galleries and the founder task board remain separate.

## Backend and content boundary

No database schema, access policy, membership, question, solution, diagram, company attribution or model configuration was changed. Existing authenticated API contracts remain in use. The only backend-directory change updates the smoke-check route inventory to include the already-existing question-report and question-resource endpoints; it does not alter the running API.

Shaked does not need to add a theme API or run a migration. Theme preference is deliberately a small browser setting, not a new database field. Keep future component colors on the semantic variables in `apps/web/src/app/ion.css`; literal white backgrounds or dark text inside editors will break the alternate theme.

## Verification

| Check | Result and scope |
| --- | --- |
| Frontend automated suite | 65 passing tests, including new first-visit dark, stored-theme and unavailable-storage tests; existing circuit, completion, API, content and draft tests remain passing. |
| Backend automated suite | 806 passing tests with `DATABASE_URL` empty and the scripted provider. The three live database/service/interview modules were excluded from this run. |
| TypeScript and production build | Passed. The production build uses the existing application environment, not the browser fixture configuration. |
| Deployed API smoke check | Passed health, authentication configuration, all 27 expected routes, allowed/forbidden CORS, unauthenticated and forged-token rejection, error contracts, payload limit and signing-key retrieval. The initial check exposed a stale expected-route list; adding the two existing routes resolved it without relaxing assertions. |
| Browser workflows | Actual frontend against the real FastAPI service layer with an isolated in-memory store, fake authentication service and scripted model. See the exercised flows below. |
| Visual checks | Desktop 1440×1000, phone 390×844 and the 849×1000 browser width; Hebrew RTL and English LTR, dark and light. No horizontal document overflow in the measured desktop/mobile views. |

Browser flows exercised: sign in, save a goal, load the daily plan, search Intel/INTEL/אינטל (all returned the same 21 fixture questions), open a question, request a hint, enter Hebrew reasoning and C code, add a circuit component and run its simulator, switch theme without losing draft state, submit an answer, receive feedback, answer a follow-up, reveal the reference, revisit progress, start a mock interview, submit an answer, end early and open the saved report. Preference retention across reload and keyboard activation of the theme control were checked.

Screenshots and the design-review record are local artifacts under `.impeccable/review/ion-production/`; temporary synthetic authentication is ignored by Git. The chip's existing asset provenance is retained. The UI detector reported three legacy layout-property transitions; they were removed.

The independent design review found two presentation fixes: flatten nested progress statistic tiles, and put learning headings before their context metadata. Both were applied and recaptured at desktop and mobile sizes. The reviewer's final disposition is **ship**, with both listed fixes scored **resolved**; that final verdict is limited to the fix list.

## What this verification does not establish

- Scripted browser feedback validates the integration and state transitions, not the quality, language accuracy or grading of a paid AI model. Fixture feedback is deliberately synthetic.
- No new paid model evaluation or private answer-photo upload was performed during this theme rollout. Existing image-handling tests passed, but live photo interpretation remains part of the human pilot.
- The isolated 806-test result must not be represented as a fresh pass of the live PostgreSQL suites.
- Some already-saved plan explanations can remain in the language in which the plan was created when the interface language changes. This behavior was observed in the fixture and is independent of theme switching.

## Release and recovery

Push this change to the existing `master` branch. The practice workflow asks Netlify to build `apps/web`; the task-board workflow is not triggered by these frontend files. Confirm the released commit through the site's `/api/health` revision and inspect the live theme toggle before calling the release complete. Never deploy the local screenshot fixture or copy its fake public configuration to Netlify.

Rollback is the previous successful Netlify deployment or a Git revert of this release; no database rollback is needed. Preserve the browser preference when iterating on styling. Future human review should include one representative correct, partial and incorrect answer, a handwritten image and a circuit in both modes.
