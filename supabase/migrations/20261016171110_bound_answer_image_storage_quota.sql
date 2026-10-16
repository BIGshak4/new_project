-- Storage checks the caller's existing RLS policy, then persists through an
-- internal role. Do not depend on auth.uid() in this persistence trigger.
-- Authorization stays in the existing INSERT policy; this additional guard
-- checks path/parent consistency and enforces an aggregate storage allowance.
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
drop trigger if exists limit_practice_answer_images on storage.objects;
create trigger limit_practice_answer_images
  before insert or update of bucket_id, name on storage.objects
  for each row execute function jobrun_private.limit_answer_images();
