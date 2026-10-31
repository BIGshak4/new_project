-- Internal execution quota/idempotency ledger. Browser roles have no direct access.
create table public.code_execution_runs (
    id uuid primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    scope text not null check (length(scope) between 1 and 180),
    idempotency_key text not null check (length(idempotency_key) between 1 and 128),
    request_hash text not null check (request_hash ~ '^[0-9a-f]{64}$'),
    created_at timestamptz not null default now(),
    finished_at timestamptz,
    result jsonb,
    unique(user_id, scope, idempotency_key)
);
create index code_execution_runs_user_time on public.code_execution_runs(user_id, created_at desc);
create index code_execution_runs_time on public.code_execution_runs(created_at desc);
alter table public.code_execution_runs enable row level security;
revoke all on public.code_execution_runs from public, anon, authenticated;
comment on table public.code_execution_runs is 'Backend-only runner facts and quotas; no learner source, testbench, ticket, or credentials.';
