-- Coins (Shaked, 2026-10-22): a spendable currency next to XP. One row per gift, earn, spend, stake, payout, refund
-- or forfeit; the balance is the sum. Backend-only writes; the browser may read its own rows.
-- Coins have no monetary value, are never bought and never cashed out (what keeps a duel a game).

create table public.coin_ledger (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references public.user_profile(id) on delete cascade,
  delta       integer not null check (delta <> 0),
  kind        varchar(12) not null check (kind in ('gift', 'earn', 'spend', 'stake', 'payout', 'refund', 'forfeit')),
  reference   text,                                   -- idempotency: answer:<attempt>:<revision>, gift, duel:<id>:stake ...
  item        varchar(40),                            -- the shop item, for a spend
  duel_id     uuid,                                   -- set by the duel rows (the duel table comes with the duels migration)
  meta        jsonb not null default '{}'::jsonb,     -- band, difficulty, the item's effect; never personal data
  created_at  timestamptz not null default now()
);
comment on table public.coin_ledger is
  'Coins per user as a ledger: gifts, earnings from strong answers, shop spends, duel stakes and payouts. Written only by the API.';
create unique index coin_ledger_reference_idx on public.coin_ledger (user_id, reference) where reference is not null;
create index coin_ledger_user_time_idx on public.coin_ledger (user_id, created_at desc);

alter table public.coin_ledger enable row level security;
revoke all on public.coin_ledger from anon, authenticated;
grant select (user_id, delta, kind, item, duel_id, created_at) on public.coin_ledger to authenticated;
create policy "coin_ledger: read own" on public.coin_ledger
  for select to authenticated using (user_id = (select auth.uid()));
