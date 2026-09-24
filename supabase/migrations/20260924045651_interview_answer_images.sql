-- Photos in the mock interview. The answer-image bucket accepted paths of the form
-- <user>/<attempt>/<file> and checked the attempt; an interview answer uses the interview
-- session id as the second segment, so the upload rule and its trigger accept an in-progress
-- interview_session of the same learner too. Shaked, 2026-09-23.

drop policy "learners upload answer images" on storage.objects;
create policy "learners upload answer images" on storage.objects for insert to authenticated
with check (
  bucket_id = 'practice-answer-images'
  and name ~ '^[0-9a-f-]{36}/[0-9a-f-]{36}/[0-9a-f-]{36}\.(jpg|png|webp)$'
  and (storage.foldername(name))[1] = (select auth.uid())::text
  and exists(select 1 from public.jr_members)
  and (
    exists(select 1 from public.attempt a where a.id::text = (storage.foldername(name))[2]
           and a.user_id = (select auth.uid()) and a.submitted_at is null)
    or exists(select 1 from public.interview_session s where s.id::text = (storage.foldername(name))[2]
              and s.user_id = (select auth.uid()) and s.status = 'in_progress')
  )
);

create or replace function jobrun_private.limit_answer_images() returns trigger
language plpgsql security definer set search_path = '' as $$
declare aid uuid; owner_uuid uuid; n integer;
begin
  if new.bucket_id <> 'practice-answer-images' then return new; end if;
  if auth.uid() is null then raise exception 'authenticated learner required'; end if;
  aid := split_part(new.name, '/', 2)::uuid;
  select user_id into owner_uuid from public.attempt where id = aid for update;
  if owner_uuid is null then
    select user_id into owner_uuid from public.interview_session where id = aid for update;
  end if;
  if owner_uuid is distinct from auth.uid() or split_part(new.name, '/', 1) <> auth.uid()::text then
    raise exception 'attempt does not belong to learner';
  end if;
  select count(*) into n from storage.objects where bucket_id = 'practice-answer-images'
    and name like auth.uid()::text || '/' || aid::text || '/%';
  if n >= 24 then raise exception 'image upload allowance reached for this attempt'; end if;
  return new;
end $$;
