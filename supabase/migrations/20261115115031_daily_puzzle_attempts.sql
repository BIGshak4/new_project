-- One immutable answer per learner and Israel calendar day. The backend owns evaluation writes.
create table public.daily_puzzle_attempt (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    puzzle_day date not null,
    puzzle_key text not null,
    status text not null default 'open' check (status in ('open', 'evaluating', 'failed', 'done')),
    language text check (language in ('en', 'he')),
    submission jsonb,
    score numeric check (score between 0 and 100),
    lease_id uuid,
    claimed_at timestamptz,
    unique(user_id, puzzle_day),
    check ((status = 'open') = (submission is null)),
    check ((status = 'done') = (score is not null)),
    check ((status = 'evaluating') = (lease_id is not null)),
    check ((status = 'evaluating') = (claimed_at is not null))
);
alter table public.daily_puzzle_attempt enable row level security;
revoke all on public.daily_puzzle_attempt from public, anon, authenticated;
grant select (id, user_id, puzzle_day, status) on public.daily_puzzle_attempt to authenticated;
grant select, insert, update, delete on public.daily_puzzle_attempt to service_role;
create policy "learner reads own daily puzzle upload scope" on public.daily_puzzle_attempt
    for select to authenticated using (user_id = (select auth.uid()));

-- Separate from the practice/interview policy so their existing access rules remain intact.
create policy "learners upload daily puzzle answers" on storage.objects for insert to authenticated
with check (
    bucket_id = 'practice-answer-images'
    and (storage.foldername(name))[1] = (select auth.uid())::text
    and exists (select 1 from public.daily_puzzle_attempt a
        where a.user_id = (select auth.uid()) and a.id::text = (storage.foldername(name))[2]
          and a.status = 'open' and a.puzzle_day = (now() at time zone 'Asia/Jerusalem')::date)
);

create or replace function jobrun_private.limit_answer_images() returns trigger
language plpgsql security definer set search_path = '' as $$
declare
  parent_id uuid;
  path_owner uuid;
  parent_owner uuid;
  parent_open boolean;
  object_limit integer;
  object_count bigint;
  object_prefix text;
  replaced_id uuid;
begin
  if new.bucket_id <> 'practice-answer-images' then return new; end if;
  if tg_op = 'UPDATE' then
    if new.bucket_id = old.bucket_id and new.name = old.name then return new; end if;
    replaced_id := old.id;
  end if;

  -- Canonical UUID segments and a raster extension, matching browser locators.
  if new.name !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[.](jpg|png|webp)$' then
    raise exception 'invalid answer image locator' using errcode = 'check_violation';
  end if;
  path_owner := split_part(new.name, '/', 1)::uuid;
  parent_id := split_part(new.name, '/', 2)::uuid;

  -- A shared parent row lock serializes uploads, including across API workers.
  -- It also serializes with completion, so an upload cannot race parent closure.
  select user_id, submitted_at is null into parent_owner, parent_open
    from public.attempt where id = parent_id for update;
  if found then
    object_limit := 24;
  else
    select user_id, status = 'in_progress' into parent_owner, parent_open
      from public.interview_session where id = parent_id for update;
    -- Interviews allow 40 turns x 4 answer images, plus replacement headroom.
    object_limit := 200;
    if not found then
      select user_id, status = 'open' and puzzle_day = (now() at time zone 'Asia/Jerusalem')::date
        into parent_owner, parent_open from public.daily_puzzle_attempt where id = parent_id for update;
      object_limit := 24;
    end if;
  end if;
  if parent_owner is distinct from path_owner or parent_open is distinct from true then
    raise exception 'answer image parent is unavailable' using errcode = 'check_violation';
  end if;

  object_prefix := path_owner::text || '/' || parent_id::text || '/';
  select count(*) into object_count from storage.objects
    where bucket_id = 'practice-answer-images' and name like object_prefix || '%'
      and (replaced_id is null or id <> replaced_id);
  if object_count >= object_limit then
    raise exception 'answer image upload allowance reached' using errcode = 'check_violation';
  end if;
  return new;
end $$;

revoke all on function jobrun_private.limit_answer_images() from public, anon, authenticated;
