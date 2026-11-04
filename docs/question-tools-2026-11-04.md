# Question actions and answer tools — 2026-11-04

The long question workspace, mock interview, quick fundamentals and multiple-choice game now share a visible question-report frame. Its three actions are **Report a problem**, **Unclear question**, and **Seen at a company**, with matching Hebrew labels.

Long-bank questions retain their direct question-report and company-sighting APIs. Short and quiz questions use the existing support inbox with their exact question key, title, context and quiz variant. The report remains a user-submitted draft; clicking a shortcut does not send it. An existing unsent report keeps its original question context until the user explicitly chooses to replace it. Reports remain authenticated and existing upload/privacy protections remain in place.

Explanation, code/formulas, circuit and image inputs start closed, including restored drafts. Follow-up answer fields also start closed and reset for each new turn. Each has a separate disclosure button, expanded state and content indicator. Closing preserves input data and mounted editor history; closing the explanation also stops dictation. Changing questions resets disclosure state. Submitted answers remain readable. The helper and guided tour point to the opening control when an editor is closed.

Validation used real `PracticeSession`, `QuickPractice` and game components, with a local stub for the practice API and the existing game preview. It covered the closed default, restored explanation/code, circuit undo after close/reopen, image tools, question actions, and Hebrew/English light/dark layouts. At a 388 CSS-pixel viewport the report controls remain within the viewport and retain approximately 44-pixel touch targets. Production report submission was not exercised, so no test messages were sent to the founders.

Browser evidence is stored locally under `.impeccable/review/question-tools-20261104/`. Temporary browser-check routes were removed before the production build.

Question content edits and their integrity checks are separate from UI behavior. Live long-bank copy synchronization uses `backend/scripts/prepare_question_copy_sync.py`: offline planning from backed-up rows, exact baseline comparison, rollback dry runs, canary and small transactions with row locks and full before/after guards. It never writes user progress, attempts, skill links, review status or assessment-readiness flags. An attestation tied to an old content fingerprint is invalidated rather than relabeled as current.
