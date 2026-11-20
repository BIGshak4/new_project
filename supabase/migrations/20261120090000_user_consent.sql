-- The consent a user gives at sign-up (personalisation; backend/app/services/legal.py, backend/seeds/legal/).
-- One row is the proof the legal checklist asks for: who agreed (the verified account), when (this database's
-- clock), to which version of which text, in which language, from which screen. No IP address is kept.
-- Only the API writes and reads it; the browser has no access. Rows are never updated: a new text version is a
-- new row. Closing the account removes its rows with it.
create table public.user_consent (
    user_id uuid not null references auth.users(id) on delete cascade,
    consent_key text not null check (consent_key ~ '^[a-z_]{1,40}$'),
    version text not null check (char_length(version) between 1 and 40),
    policy_version text not null check (char_length(policy_version) between 1 and 40),
    language text not null check (language in ('he', 'en')),
    source text not null check (source in ('signup', 'prompt')),
    accepted_at timestamptz not null default now(),
    primary key (user_id, consent_key, version)
);

comment on table public.user_consent is 'Proof of a consent given by a user: text key and version, language shown, screen, server time. Written by the API only.';

alter table public.user_consent enable row level security;
revoke all on public.user_consent from public, anon, authenticated;
grant select, insert on public.user_consent to service_role;
