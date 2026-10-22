-- Duels (Shaked, 2026-10-22): two players stake five coins each on one short question neither has seen; the same
-- judge scores both; the better band wins the pot, a tie goes to the faster answer, a tie again refunds both.
-- A no-show forfeits. Backend-only writes; no browser read: the API shows each player their own view and hides the
-- opponent's answer until the duel is settled. Coins have no monetary value (see 20261022090000_coins.sql).

create table public.duel (
  id             uuid primary key default gen_random_uuid(),
  code           varchar(16) not null unique,            -- the invite code in the link
  status         varchar(12) not null check (status in ('open', 'active', 'settled', 'cancelled')),
  challenger_id  uuid not null references public.user_profile(id) on delete cascade,
  opponent_id    uuid references public.user_profile(id) on delete set null,
  language       varchar(2) not null default 'he',
  stake          integer not null check (stake > 0),
  clock_seconds  integer not null check (clock_seconds > 0),
  question_key   text,                                   -- chosen when the opponent accepts: unseen by both
  created_at     timestamptz not null default now(),
  accepted_at    timestamptz,
  deadline       timestamptz,
  settled_at     timestamptz,
  outcome        varchar(20) check (outcome is null or outcome in
                   ('challenger', 'opponent', 'draw', 'forfeit_challenger', 'forfeit_opponent', 'no_show', 'cancelled', 'expired')),
  winner_id      uuid references public.user_profile(id) on delete set null,
  players        jsonb not null default '{}'::jsonb,     -- user id -> {answer, band, submitted_at, summary, flags, model}
  meta           jsonb not null default '{}'::jsonb,
  version        integer not null default 0              -- optimistic: two answers landing together cannot both settle
);
comment on table public.duel is
  'A coin duel between two users on one bank question. Written only by the API; each player reads their own view through it.';
create index duel_challenger_idx on public.duel (challenger_id, created_at desc);
create index duel_opponent_idx on public.duel (opponent_id, created_at desc);
create index duel_open_idx on public.duel (status, created_at) where status in ('open', 'active');

alter table public.duel enable row level security;
revoke all on public.duel from anon, authenticated;
