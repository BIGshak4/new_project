create table public.question_resume_visits (
    user_id uuid not null references auth.users(id) on delete cascade,
    kind text not null check (kind in ('practice','quick')),
    question_key text not null check (length(question_key) between 1 and 160),
    attempt_id uuid,
    visited_at_ms bigint not null check (visited_at_ms between 1 and 8640000000000000),
    dismissed boolean not null,
    primary key (user_id, kind, question_key),
    check (kind = 'practice' or attempt_id is null)
);
create index question_resume_recent on public.question_resume_visits(user_id, visited_at_ms desc)
    where not dismissed;
alter table public.question_resume_visits enable row level security;
revoke all on public.question_resume_visits from public, anon, authenticated;
grant select, insert, update on public.question_resume_visits to authenticated;
create policy "read own visits" on public.question_resume_visits for select to authenticated
    using (user_id = (select auth.uid()));
create policy "insert own visits" on public.question_resume_visits for insert to authenticated
    with check (user_id = (select auth.uid()));
create policy "update own visits" on public.question_resume_visits for update to authenticated
    using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));

-- A late write from another tab cannot revive an older view after submission.
create function public.sync_question_resume_visits(p_owner uuid, p_events jsonb)
returns void language plpgsql security invoker set search_path = '' as $$
begin
    if p_owner is distinct from auth.uid() or p_owner is null then
        raise exception 'account changed' using errcode = '42501';
    end if;
    if jsonb_typeof(p_events) is distinct from 'array' or jsonb_array_length(p_events) > 64 then
        raise exception 'invalid visits' using errcode = '22023';
    end if;
    insert into public.question_resume_visits as saved
        (user_id, kind, question_key, attempt_id, visited_at_ms, dismissed)
    select p_owner, e.kind, e.question_key, e.attempt_id, e.visited_at_ms, e.dismissed
    from jsonb_to_recordset(p_events) as e(kind text, question_key text, attempt_id uuid, visited_at_ms bigint, dismissed boolean)
    order by e.kind, e.question_key
    on conflict (user_id, kind, question_key) do update set
        attempt_id = case when not excluded.dismissed and not saved.dismissed
                          then coalesce(excluded.attempt_id, saved.attempt_id) else excluded.attempt_id end,
        visited_at_ms = excluded.visited_at_ms, dismissed = excluded.dismissed
    where (excluded.visited_at_ms > saved.visited_at_ms or
          (excluded.visited_at_ms = saved.visited_at_ms and excluded.dismissed and not saved.dismissed))
      and (not excluded.dismissed or excluded.attempt_id is null or excluded.attempt_id is not distinct from saved.attempt_id);
end;
$$;
revoke all on function public.sync_question_resume_visits(uuid,jsonb) from public, anon, authenticated;
grant execute on function public.sync_question_resume_visits(uuid,jsonb) to authenticated;
