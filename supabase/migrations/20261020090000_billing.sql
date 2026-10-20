-- Paying for the site (Shaked, 2026-10-20): one subscription row per user, one row per Stripe event handled.
-- Backend-only writes (the Stripe webhook and the checkout flow). The browser may read its own subscription row.
-- Nothing here makes payment mandatory: that is the API's REQUIRE_PAYMENT switch.

create table public.billing_subscription (
  user_id               uuid primary key references public.user_profile(id) on delete cascade,
  status                varchar(16) not null default 'free'
                        check (status in ('free', 'active', 'trialing', 'past_due', 'canceled', 'expired')),
  plan                  varchar(40),                       -- a key from backend/seeds/billing_plans.json
  customer_id           text,                              -- Stripe customer id (cus_...)
  subscription_id       text,                              -- Stripe subscription id (sub_...); null for a one-time package
  period_end            timestamptz,                       -- paid through; null = open-ended while active
  cancel_at_period_end  boolean not null default false,
  updated_at            timestamptz not null default now()
);
comment on table public.billing_subscription is
  'Paid access per user, written only by the API from Stripe events. No card data: Stripe holds the payment method.';
create unique index billing_subscription_customer_idx on public.billing_subscription (customer_id) where customer_id is not null;

create table public.billing_event (
  id            text primary key,                          -- the Stripe event id (evt_...): applied once, Stripe retries deliveries
  kind          text not null,
  user_id       uuid references public.user_profile(id) on delete set null,
  summary       jsonb not null default '{}'::jsonb,        -- ids, status, amounts; never a card, never an address
  received_at   timestamptz not null default now()
);
comment on table public.billing_event is 'Every Stripe webhook event the API applied, by event id, for idempotency and audit.';
create index billing_event_user_idx on public.billing_event (user_id, received_at desc);

alter table public.billing_subscription enable row level security;
alter table public.billing_event enable row level security;
revoke all on public.billing_subscription from anon, authenticated;
revoke all on public.billing_event from anon, authenticated;
-- the browser may read its own paid status (the API is the writer)
grant select (user_id, status, plan, period_end, cancel_at_period_end, updated_at) on public.billing_subscription to authenticated;
create policy "billing_subscription: read own" on public.billing_subscription
  for select to authenticated using (user_id = (select auth.uid()));
