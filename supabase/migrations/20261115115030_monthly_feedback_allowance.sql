-- The API reserves one feedback use before calling the judge. A reference identifies
-- either a bank practice attempt or a daily puzzle attempt across retries.
create table public.feedback_allowance_use (
    user_id uuid not null references auth.users(id) on delete cascade,
    reference_id uuid not null,
    period date not null,
    primary key (user_id, reference_id)
);
create index feedback_allowance_use_period on public.feedback_allowance_use(user_id, period);
alter table public.feedback_allowance_use enable row level security;
revoke all on public.feedback_allowance_use from public, anon, authenticated;
grant select, insert, delete on public.feedback_allowance_use to service_role;
