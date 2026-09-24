-- "I saw it at company X": candidates tag a question with the company where they met it, and everyone
-- can then search the bank by company. One row per (question, user, company); the backend writes it
-- through the API and aggregates counts per question. Shaked, 2026-09-23.

create table public.question_sighting (
  id             uuid primary key default gen_random_uuid(),
  question_id    uuid not null references public.question(id) on delete cascade,
  user_id        uuid not null references public.user_profile(id) on delete cascade,
  company_name   varchar(80) not null check (length(btrim(company_name)) between 1 and 80),
  company_slug   varchar(80) not null check (company_slug ~ '^[a-z0-9א-ת]+(-[a-z0-9א-ת]+)*$'),   -- same alphabet as app/repo/sightings.slugify
  created_at     timestamptz not null default now(),
  constraint question_sighting_uq unique (question_id, user_id, company_slug)
);
comment on table public.question_sighting is
  'A candidate reporting that a bank question was asked at a company. Aggregated per question for search; never shown per user.';

create index question_sighting_company_idx  on public.question_sighting (company_slug, question_id);
create index question_sighting_question_idx on public.question_sighting (question_id);

alter table public.question_sighting enable row level security;
revoke all on public.question_sighting from anon, authenticated;   -- backend only; the API exposes aggregates
