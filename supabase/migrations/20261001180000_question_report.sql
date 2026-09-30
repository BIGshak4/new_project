-- A candidate flagging a bank question as unclear (or wrong), with an optional note, so the team can fix it later.
-- Backend-only writes, like question_sighting. One report per user per question per reason; a second press updates the note.

create table public.question_report (
  id             uuid primary key default gen_random_uuid(),
  question_id    uuid not null references public.question(id) on delete cascade,
  user_id        uuid not null references public.user_profile(id) on delete cascade,
  reason         varchar(24) not null check (reason in ('unclear', 'wrong', 'other')),
  note           varchar(500),
  language       varchar(2) not null check (language in ('he', 'en')),
  context        varchar(24) not null default 'practice' check (context in ('practice', 'interview', 'library')),
  created_at     timestamptz not null default now(),
  resolved_at    timestamptz,
  resolved_by    text,
  constraint question_report_uq unique (question_id, user_id, reason)
);
comment on table public.question_report is
  'A candidate saying a bank question is unclear or wrong, with an optional note. Read by the review tooling; never shown to other users.';
create index question_report_open_idx on public.question_report (question_id) where resolved_at is null;
alter table public.question_report enable row level security;
revoke all on public.question_report from anon, authenticated;   -- backend only
