-- Storage authorizes through RLS, then persists with its internal role.
-- Enforce ownership in policies; a trigger requiring auth.uid() also rejects authorized uploads.
drop trigger if exists limit_practice_answer_images on storage.objects;
drop function if exists jobrun_private.limit_answer_images();
