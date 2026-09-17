# JobRun Founder Tasks

Private Hebrew task board: https://jobrun-tasks.netlify.app.

Use Node.js 24. Copy `.env.example` to `.env.local`, run `npm ci`, then `npm run dev -- --port 3001`. `npm run build` validates TypeScript and produces the production application.

Access requires a confirmed Supabase account plus a `jr_members` row with `can_manage_tasks=true`. All authorization is enforced by database/storage policies, independently of the client UI.

Tasks save individually with an expected version. Conflicts preserve the local draft instead of silently overwriting another person's work. Drafts are tab-local, not a cross-device backup. Files are private and downloaded with short-lived signed URLs. Task JSON export contains task rows only; comments, events and uploaded files are not included.

See [operations guide](../../docs/netlify-and-supabase.md) for deployment and access setup.
