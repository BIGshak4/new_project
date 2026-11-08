# Muxi guided tours

The public route `/tour` lets visitors try JobRun before signup. The signed-in **Tour with Muxi** launcher opens a single account walkthrough. Both work in Hebrew and English, including on phones. The tour stays optional on account entry.

The visitor explores an interview question and a short fundamentals question, completes a three-sensor alarm in the circuit editor, and generates its truth table. Two consecutive software stops use the same array maximum question. The visitor submits a written explanation, reads feedback prepared for the sample, then checks a repair in the code editor. A one-question written interview ends with an explicitly prewritten report. The personal helper appears only after sign-in. Visitors can skip stations, pause and return, or follow the link to signup.

The member tour starts with the account’s existing goal. Members can keep a complete goal, edit it, or configure a new one with the same form the personal area uses. Opening the tour does not write to the account. Saving the goal explicitly updates the personal plan. The remaining exercises use sample data, including demonstrations of friends, the avatar shop and the personal helper. Existing drafts and the underlying workspace stay mounted while the tour is open. Ordinary practice, scores, XP and purchases are separate from these demonstrations.

The public and per-user checkpoints are versioned independently in local browser storage. Only station progress is persisted. Old short/full checkpoints start afresh in the updated tutorials. Visitors can still use the tour when storage is unavailable. Muxi’s gestures respond to a change of station or completion; reduced-motion preferences keep the same textual guidance.

From `apps/web`, use these commands with a local web server and the existing screenshot-server fixture:

```powershell
npm test
node tools/tours/verify.mjs http://localhost:3291 C:/path/to/preview-output
node tools/tours/verify-host.mjs http://localhost:3291 C:/path/to/fixture-session.json
```

The guest verifier traverses the preview on desktop and phone, checks sample interactions, resume and the sign-in destination, and checks for unexpected account or model requests. The host verifier checks the real account-goal request against the in-memory fixture, dashboard refresh, an existing draft, tour replay, the personal helper, and nested circuit dialogs. Use `PLAYWRIGHT_MODULE` / `EDGE_EXECUTABLE` for the guest verifier and `PLAYWRIGHT_PACKAGE_ROOT` / `EDGE_PATH` for the host verifier to select a local Playwright installation and browser.
