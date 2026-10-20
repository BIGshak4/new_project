# JobRun Admin

Private Hebrew founder workspace: https://jobrun-tasks.netlify.app. The existing URL and task data remain unchanged.

Use Node.js 24. Copy `.env.example` to `.env.local`, run `npm ci`, then `npm run dev -- --port 3001`. `npm run build` validates TypeScript and produces the production application.

From the repository root, run `node --test tools/qa/admin-reply-concurrency.test.mjs` for the public-reply lost-response/concurrent-edit regressions. The tests execute the actual production reconciliation helper without browser credentials or a database connection.

Access requires a confirmed Supabase account plus a `jr_members` row with `can_manage_tasks=true`. All authorization is enforced by database/storage policies, independently of the client UI.

The workspace includes:

- The original task board and archive, assignees, due dates, subtasks, comments, private files and version history.
- A searchable, paginated user directory with email confirmation, signup/last-sign-in dates, pilot access and plan. Founders can set `free`, `pro` or `team` manually. These are administrative entitlements only: changing them does not collect payment, create a paid subscription, or integrate a payment processor. Founder access is protected in both the interface and database.
- A searchable support queue with status filters, reporter/page/question context, private attachment downloads, priority, a founder assignee, internal notes, resolution and an audit timeline. A separate section includes existing “unclear question” reports and allows marking them handled or reopening them.
- A founder-only “Updates for users” section with a searchable announcement list, draft/save/publish/archive lifecycle and Hebrew/English wording. Hebrew title/body are required; English is optional but must include both fields. Without English, the original Hebrew is shown with its language identified. Publication requires a saved, unchanged draft and an explicit confirmation of the audience. Published wording is immutable; corrections use a new announcement. No email is sent.

The new administration operations use narrowly scoped Supabase RPCs from `20261020191024_founder_admin_and_support.sql`. Use the same public Supabase environment variables from `.env.example`; no backend service key or new secret environment variable belongs in this browser application. Changes require the migration to be applied before the administration sections can load.

Switching between tasks, users and support keeps editing state mounted. Switching to another user/report or closing an unsaved editor asks before discarding its changes. Administrative saves use expected values/versions: if another founder saved first, the local edit stays in the form and the interface offers comparison before another save. Report/user drafts are in-memory and warn before closing the browser; only task drafts have the existing tab-local storage recovery.

Support attachments use the separate private `jr-support-files` bucket: PNG, JPEG, WebP, PDF or plain text, at most 5 MB per file, 5 files and 15 MB per report. Downloads use signed URLs valid for 60 seconds. File type/size, report ownership and quota are enforced by the database and storage policies, not only by the upload form. Internal notes are founder-only. No automatic email is sent when handling a report.

User updates and public support responses require the additive `user_updates_and_support_inbox` migration as well. The support detail clearly separates **Reply to the user**, **Internal notes** and the public handling summary. Reply text, status changes and resolution text appear in the reporter's private in-app updates; assignees, priority, internal notes and the administrative audit never do. Resolving or closing a report requires a nonblank public explanation. Internal-only saves do not notify the user.

Public reply submissions use an explicit UUID idempotency key and the expected report version. If the response is uncertain, the original request is kept and the retry uses the same UUID and text. Pending public replies are recovered from tab-local storage scoped to the founder and report; this is not a cross-device backup. Announcement failures preserve the wording and require reading the authoritative saved version before another action after an uncertain result. No automated QA should publish test announcements to real users: use isolated fixtures or roll back a database test transaction instead.

Tasks save individually with an expected version. Conflicts preserve the local draft instead of silently overwriting another person's work. Drafts are tab-local, not a cross-device backup. Files are private and downloaded with short-lived signed URLs. Task JSON export contains task rows only; comments, events and uploaded files are not included.

See [operations guide](../../docs/netlify-and-supabase.md) for deployment and access setup.
