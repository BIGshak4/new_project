-- ============================================================================
-- 1100  Practice submissions and restart recovery (backend step 4b)
-- Source: docs/backend-review-for-shaked.md R1-R3, backend/app/engine/practice.py
--
-- An attempt now has answer REVISIONS. Each revision is accepted once (idempotency
-- key), evaluated with its own status, and stores what the candidate was shown, so a
-- refresh or a server restart replays the same result without another model call.
--
--   attempt_submission          one row per accepted answer revision
--   attempt.exposures           the hint/reveal log (evidence is bound to it)
--   attempt.engine_state        small engine state needed to restore an attempt
--   user_skill_profile.version  optimistic versioning: concurrent updates cannot
--                               silently overwrite each other
--
-- The unique (attempt_id, idempotency_key) constraint is what makes "scored exactly
-- once" hold across two server instances, not only inside one process.
-- ============================================================================

create table public.attempt_submission (
  id                 uuid primary key default gen_random_uuid(),
  attempt_id         uuid not null references public.attempt(id) on delete cascade,
  revision           smallint not null check (revision >= 1),
  idempotency_key    varchar(128) not null check (length(idempotency_key) between 1 and 128),
  turn               smallint not null default 0 check (turn >= 0),          -- 0 = main question, n = n-th follow-up
  answer             text not null check (length(answer) between 1 and 20000),
  hints_seen         smallint not null default 0 check (hints_seen between 0 and 3),
  reference_seen     boolean not null default false,
  exposure_sequence  integer not null default 0 check (exposure_sequence >= 0),
  status             varchar(12) not null default 'pending'
                     check (status in ('pending', 'evaluating', 'done', 'failed')),
  attempts           smallint not null default 0 check (attempts >= 0),      -- evaluation tries
  accepted_at        timestamptz not null default now(),
  evaluated_at       timestamptz,
  band               public.answer_band,
  evaluation         jsonb,                                                  -- the evaluator's scores (internal)
  check_result       jsonb,
  evidence_weight    numeric(4,3) not null default 0 check (evidence_weight between 0 and 2),
  card               jsonb,                                                  -- feedback card shown to the candidate
  tip_key            varchar(80),
  tip_text           text,
  follow_up          text,                                                   -- the follow-up question this revision produced
  flags              text[] not null default '{}',

  constraint attempt_submission_revision_uq  unique (attempt_id, revision),
  constraint attempt_submission_key_uq       unique (attempt_id, idempotency_key),
  constraint attempt_submission_done_chk     check (status <> 'done' or (band is not null and evaluation is not null)),
  constraint attempt_submission_eval_obj_chk check (evaluation is null or jsonb_typeof(evaluation) = 'object'),
  constraint attempt_submission_card_obj_chk check (card is null or jsonb_typeof(card) = 'object')
);

comment on table  public.attempt_submission is
  'One accepted answer revision of a practice attempt. Immutable once accepted; only evaluation state changes. Replays by idempotency key return the stored result.';
comment on column public.attempt_submission.idempotency_key is
  'Client-chosen key (or generated). Unique per attempt: the same key twice is a replay, never a second score.';
comment on column public.attempt_submission.hints_seen is
  'Exposure snapshot at acceptance. Evidence for this revision is computed from this, not from later peeking.';

-- ---------------------------------------------------------------------------- attempt additions
alter table public.attempt
  add column exposures    jsonb not null default '[]'::jsonb,
  add column engine_state jsonb not null default '{}'::jsonb,
  add constraint attempt_exposures_array_chk    check (jsonb_typeof(exposures) = 'array'),
  add constraint attempt_engine_state_object_chk check (jsonb_typeof(engine_state) = 'object');

comment on column public.attempt.exposures is
  'Ordered hint/reveal events [{sequence, kind, level, at}]. hints_used and reference_revealed are derived from it.';
comment on column public.attempt.engine_state is
  'Small engine state needed by PracticeAttempt.restore(): evidence_mode, tip_turns. Never shown to the user.';

-- daily allowance: "attempts started today by this user" (created_at >= day_start pattern)
create index attempt_user_started_idx on public.attempt (user_id, started_at desc);

-- ---------------------------------------------------------------------------- optimistic versioning
alter table public.user_skill_profile
  add column version integer not null default 1 check (version >= 1);

comment on column public.user_skill_profile.version is
  'Bumped on every write. The backend updates with "where version = :seen"; zero rows means someone else wrote first.';

-- ---------------------------------------------------------------------------- access
-- Same model as 1000_rls: the backend (service role) is the only writer; a signed-in
-- user may read their own submissions minus the internal columns (raw evaluation
-- scores, evidence weight, evaluation try count).
alter table public.attempt_submission enable row level security;
revoke all on public.attempt_submission from anon, authenticated;
grant select (
  id, attempt_id, revision, turn, answer, hints_seen, reference_seen, status,
  accepted_at, evaluated_at, band, check_result, card, tip_key, tip_text, follow_up, flags
) on public.attempt_submission to authenticated;

create policy "attempt_submission: read own"
  on public.attempt_submission for select to authenticated
  using (
    exists (select 1 from public.attempt a where a.id = attempt_id and a.user_id = (select auth.uid()))
  );
