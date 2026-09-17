# Supabase database

The schema for the platform lives in `migrations/`, one SQL file per group, in
dependency order. These files are the source of truth: the hosted database is
rebuilt from them, never edited by hand.

| File | Creates |
|---|---|
| `..._enums.sql` | Every enum type, `set_updated_at()`, `enforce_skill_node_type()` |
| `..._skill_catalog.sql` | `skill`, `skill_dependency` |
| `..._users.sql` | `user_profile` (1:1 with `auth.users`) and the signup trigger |
| `..._roles_companies.sql` | `role_template`, `role_skill_set`, `company_profile`, `company_evidence`, `company_skill_set` |
| `..._question_bank.sql` | `question`, `question_skill`, `question_translation`, `term_glossary` |
| `..._tips.sql` | `tips_library` |
| `..._sessions.sql` | `interview_session`, `session_skill_plan`, `session_turn`, `attempt`, `delivered_tip`, `user_document` |
| `..._evaluation.sql` | `evaluation_metrics`, `user_skill_assessment`, `skill_set_scorecard`, `user_skill_profile`, `session_report` |
| `..._plan_engagement.sql` | `learning_plan`, `plan_item`, `daily_challenge`, `user_engagement`, `notification`, `usage_event` |
| `..._rls.sql` | Row-level security and column grants on every table |
| `..._seed_structure.sql` | The six launch subjects and the Generic company |

The full spec for every column is `src/Data_Models.md`.

## Applying migrations

**From Claude Code** (how the project database was first built): the Supabase
MCP connection in `.mcp.json` applies each file with `apply_migration`, which
records it in the project's migration history.

**From the Supabase CLI** (to rebuild, or for a second environment):

```powershell
npx supabase login
npx supabase link --project-ref djpwvqpsqbkvprlncjjg
npx supabase db push
```

`db push` applies only the files not yet recorded in the remote history.

## Rules

- Never edit an applied migration. Add a new file with a later timestamp.
- Timestamps are `YYYYMMDDHHMMSS`; keep them increasing.
- The backend connects with the service role and is the only writer for
  content, sessions, attempts and evaluation tables. Clients read their own
  rows through RLS.
- The skill catalog, roles and companies are seeded from `backend/seeds/`
  by `backend/scripts/seed_db.py`, not from migrations.
