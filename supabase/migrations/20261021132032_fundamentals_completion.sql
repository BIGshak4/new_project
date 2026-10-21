-- Short self-study history, written only through the authenticated backend.
-- A completion is the learner's own 'finished' marker, never correctness,
-- mastery evidence, XP, an assessment attempt or a human content approval.
create table public.fundamentals_completion (
    user_id uuid not null references auth.users(id) on delete cascade,
    question_key text not null check (question_key ~ '^[a-z0-9][a-z0-9-]{0,95}$'),
    content_revision text not null check (content_revision ~ '^[a-f0-9]{64}$'),
    completed_at timestamptz not null default now(),
    primary key (user_id, question_key)
);
comment on table public.fundamentals_completion is
    'Self-reported short-card completion per learner, with content revision. Backend validates known keys and revisions. No grading or XP.';

alter table public.fundamentals_completion enable row level security;
revoke all on public.fundamentals_completion from public, anon, authenticated, service_role;
grant select, insert, update, delete on public.fundamentals_completion to service_role;
-- MAINTAIN is available in PostgreSQL 17+. Revoke it explicitly on that version
-- too; browser roles have no table-maintenance or direct data privileges.
do $$
begin
    if current_setting('server_version_num')::integer >= 170000 then
        execute 'revoke maintain on public.fundamentals_completion from public, anon, authenticated, service_role';
    end if;
end $$;

-- Defense in depth if a future migration intentionally grants direct access.
-- Current browser roles remain ungranted so they cannot bypass API catalog
-- validation by writing an invented question key or content revision.
create policy "fundamentals_completion: read own" on public.fundamentals_completion
    for select to authenticated using (user_id = (select auth.uid()));
create policy "fundamentals_completion: insert own" on public.fundamentals_completion
    for insert to authenticated with check (user_id = (select auth.uid()));
create policy "fundamentals_completion: update own" on public.fundamentals_completion
    for update to authenticated using (user_id = (select auth.uid()))
    with check (user_id = (select auth.uid()));
create policy "fundamentals_completion: delete own" on public.fundamentals_completion
    for delete to authenticated using (user_id = (select auth.uid()));
