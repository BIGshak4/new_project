# Practice loading and help controls — 2026-09-19

## Changes

- The question bank renders as soon as its request completes; progress, saved notes, and server health load independently. Unknown counters display a dash instead of zero. Failed background requests can be retried.
- A versioned, user- and language-scoped `sessionStorage` cache displays catalog summaries while refreshing. It expires after 12 hours and contains only an explicit allowlist of catalog metadata. It does not contain question bodies, hidden hints, solutions, submissions, or skill assessments. Attempts and all assessment actions still require the authenticated API.
- The compact EN / עב control is in the workspace toolbar and the sign-in header, rather than floating over page content.
- Question preview leads with the actual question, followed by a single “Write my answer” action. An inline link near the title jumps to that action for long questions. Practice options are collapsed by default, with plain-language explanations of follow-ups and optional confidence labels. Unselected confidence is omitted from the API request rather than silently rated 3/5. Starting focuses the answer field. Active attempts keep hint and solution buttons near the question title; they remain separate, explicit exposure actions.
- Removed the “Question requirements” disclosure. Some authored `requirements` contain expected outputs or solution details. `repo.questions.detail()` now returns an empty compatibility field for every detail/attempt response. The full server-side bank object retains requirements for grading; this does not change the evaluator or database content.

## Hosting limitation

`render.yaml` still selects a free Render web service. Render documents that free web services sleep after 15 minutes without inbound traffic and take about a minute to wake: https://render.com/docs/free.

Independent loading and the summary cache improve navigation and revisits, but cannot guarantee an immediate first uncached load or attempt creation while the API sleeps. Removing that cold-start delay requires an always-on service instance (or a separate architecture change). No paid plan was activated. Changing the workspace plan alone is not the same as changing this service's instance type.

## Verification

- Frontend: 11 tests passed; TypeScript and production build passed.
- Backend: 518 tests passed, 16 live/environment-dependent tests skipped. New HTTP regressions cover both languages and question, new-attempt, and restored-attempt responses.
- Local UI backed by the real staging API: desktop and 390px mobile inspection; both language directions; a disposable user's attempt, first hint, and explicit solution reveal. Founder practice data was not used for these actions.

## Content authoring

Put every candidate-facing constraint in the question `prompt`. Keep grading expectations in `requirements` and references, and reveal the latter only through the reference endpoint. If separately structured public constraints are needed later, add and review a dedicated public field rather than re-exposing the grading field.
