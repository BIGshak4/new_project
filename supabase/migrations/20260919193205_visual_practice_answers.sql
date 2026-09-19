-- Visual submissions are immutable snapshots. The API is their only writer.
alter table public.attempt_submission add column visual_answer jsonb;
alter table public.attempt_submission add constraint visual_answer_object
  check (visual_answer is null or (jsonb_typeof(visual_answer) = 'object' and octet_length(visual_answer::text) <= 100000));
-- Existing column grants intentionally do not expose this new field through REST.
-- Read it through the owner-checked practice API.

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('practice-answer-images', 'practice-answer-images', false, 5242880,
        array['image/jpeg','image/png','image/webp']);

create policy "learners read own answer images" on storage.objects for select to authenticated
using (bucket_id = 'practice-answer-images' and (storage.foldername(name))[1] = (select auth.uid())::text);

create policy "learners upload answer images" on storage.objects for insert to authenticated
with check (
  bucket_id = 'practice-answer-images'
  and name ~ '^[0-9a-f-]{36}/[0-9a-f-]{36}/[0-9a-f-]{36}\.(jpg|png|webp)$'
  and (storage.foldername(name))[1] = (select auth.uid())::text
  and exists(select 1 from public.jr_members)
  and exists(select 1 from public.attempt a where a.id::text = (storage.foldername(name))[2]
             and a.user_id = (select auth.uid()) and a.submitted_at is null)
);

-- No UPDATE/DELETE policy: accepted images cannot be replaced or removed in a
-- race with submission. Removing a draft attachment only detaches its locator.
-- Maintenance removes unreferenced objects via the Storage API (never raw SQL).
-- This internal trigger serializes the upload allowance per attempt. A definer
-- is needed for the row lock on the backend-owned attempt, not for client reads.
create function jobrun_private.limit_answer_images() returns trigger
language plpgsql security definer set search_path = '' as $$
declare aid uuid; owner_uuid uuid; n integer;
begin
  if new.bucket_id <> 'practice-answer-images' then return new; end if;
  if auth.uid() is null then raise exception 'authenticated learner required'; end if;
  aid := split_part(new.name, '/', 2)::uuid;
  select user_id into owner_uuid from public.attempt where id = aid for update;
  if owner_uuid is distinct from auth.uid() or split_part(new.name, '/', 1) <> auth.uid()::text then
    raise exception 'attempt does not belong to learner';
  end if;
  select count(*) into n from storage.objects where bucket_id = 'practice-answer-images'
    and name like auth.uid()::text || '/' || aid::text || '/%';
  if n >= 24 then raise exception 'image upload allowance reached for this attempt'; end if;
  return new;
end $$;
revoke all on function jobrun_private.limit_answer_images() from public, anon, authenticated;
create trigger limit_practice_answer_images before insert on storage.objects
for each row execute function jobrun_private.limit_answer_images();
