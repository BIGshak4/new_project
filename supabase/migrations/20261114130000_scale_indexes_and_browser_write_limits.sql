-- NOT APPLIED. Dry-run only (scripts/dry_run_sql.py, 2026-11-14); waits for Shaked's approval, and for Harel's word
-- on parts 1 and 3, which touch what his web app may write. Scale and security pass of 2026-11-14:
-- backend/STATUS.md section 5zzg, security/runs/2026-11-14-scale-and-security-review.md (SEC-031 and the scale review).

-- ---------------------------------------------------------------------------------------------------------------
-- 1. question_resume_visits (SEC-031). Any signed-up account, pilot member or not, could insert rows without limit:
--    the policies checked only the owner, the question key is free text, and the 64-event bound lives in the RPC,
--    not in the table. Now: only pilot members write (the same test jr_practice_entries uses), and one account
--    holds at most 2,000 rows (the app keeps 64; two kinds times every question in the bank is about 700).
-- ---------------------------------------------------------------------------------------------------------------
alter policy "insert own visits" on public.question_resume_visits
    with check (user_id = (select auth.uid()) and exists (select 1 from public.jr_members));
alter policy "update own visits" on public.question_resume_visits
    using (user_id = (select auth.uid()))
    with check (user_id = (select auth.uid()) and exists (select 1 from public.jr_members));

create function jobrun_private.limit_question_resume_visits() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
    if exists (select 1 from (select distinct user_id from added) owners
               where (select count(*) from public.question_resume_visits v where v.user_id = owners.user_id) > 2000) then
        raise exception 'resume visit allowance reached' using errcode = 'check_violation';
    end if;
    return null;
end;
$$;
revoke all on function jobrun_private.limit_question_resume_visits() from public, anon, authenticated;
create trigger question_resume_visits_limit after insert on public.question_resume_visits
    referencing new table as added for each statement
    execute function jobrun_private.limit_question_resume_visits();

-- ---------------------------------------------------------------------------------------------------------------
-- 2. user_document (SEC-031). No app reads or writes this table; the browser could still insert rows without limit.
--    Reading one's own rows stays.
-- ---------------------------------------------------------------------------------------------------------------
drop policy if exists "user_document: insert own" on public.user_document;
drop policy if exists "user_document: delete own" on public.user_document;
revoke insert, delete on public.user_document from public, anon, authenticated;

-- ---------------------------------------------------------------------------------------------------------------
-- 3. user_profile (SEC-031). The browser may update eleven columns of its own row, among them `background`, the
--    unbounded JSON where the backend keeps the validated goal. Neither web app updates this table (both branches
--    searched, 2026-11-14): the goal is saved through POST /v1/me/goal. HAREL: confirm before this part is applied.
-- ---------------------------------------------------------------------------------------------------------------
drop policy if exists "user_profile: update own" on public.user_profile;
revoke update on public.user_profile from public, anon, authenticated;

-- ---------------------------------------------------------------------------------------------------------------
-- 4. Indexes for the reads that grow with a user's history (scale review, 2026-11-14).
--    attempt: today's count, the seen-questions window, the band counts and the daily bands become index-only.
--    coin_ledger: the balance (a sum over every row of the user, read on every screen) becomes index-only.
--    question_sighting: the per-user daily count had no index starting with the user.
-- ---------------------------------------------------------------------------------------------------------------
create index attempt_user_started_cover_idx on public.attempt (user_id, started_at desc)
    include (question_id, band, submitted_at);
drop index if exists public.attempt_user_started_idx;
create index coin_ledger_user_delta_idx on public.coin_ledger (user_id) include (delta);
create index question_sighting_user_created_idx on public.question_sighting (user_id, created_at desc);
