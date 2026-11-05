-- Deleting an interview removes it from personal history while preserving the
-- scored evidence, usage records and skill progress already earned from it.
-- This marker is independent of the engine state, so in-flight saves cannot
-- accidentally restore an entry to the history list.
alter table public.interview_session
  add column if not exists deleted_at timestamptz;

comment on column public.interview_session.deleted_at is
  'Removed from personal interview history; scored evidence and usage remain intact.';
