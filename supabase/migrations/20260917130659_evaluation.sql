-- ============================================================================
-- 0800  Evaluation
-- Source: src/Data_Models.md §9 (Evaluation_Metrics, plus §14.2 additions),
--         §7 (User_Skill_Assessment, Skill_Set_Scorecard, User_Skill_Profile),
--         §8.4 (Session_Report)
--
-- evaluation_metrics is append-only and outlives the user (anonymized, §18),
-- so user_id has no foreign key and the session/turn/attempt links are
-- ON DELETE SET NULL. Partitioning by created_at is deferred (MVP_Build_Guide §2).
-- ============================================================================

-- §9.2  Evaluation_Metrics: one row per examined skill per turn or attempt. No transcript text.
create table public.evaluation_metrics (
  id                          uuid primary key default gen_random_uuid(),
  -- container: a simulation turn OR a practice attempt
  session_id                  uuid references public.interview_session(id) on delete set null,
  turn_id                     uuid references public.session_turn(id) on delete set null,
  attempt_id                  uuid references public.attempt(id) on delete set null,
  mode                        public.activity_mode not null,           -- quick, deep, simulation, diagnostic, retention_check
  user_id                     uuid not null,                           -- no FK: replaced by an anonymized hash on deletion (§18)
  anonymized_at               timestamptz,
  -- denormalized context
  role_template_id            uuid,
  role_template_version       integer,
  company_profile_id          uuid,
  family                      public.role_family,
  sub_family                  varchar(60),
  seniority                   public.seniority,
  turn_index                  integer,
  -- skill and subject context
  subject_id                  uuid not null references public.skill(id) on delete restrict,
  subject_status_before       public.subject_status,
  subject_status_after        public.subject_status,
  subject_turns_used          smallint,
  subject_turns_planned       smallint,
  entry_difficulty_reason     jsonb,
  skill_id                    uuid not null references public.skill(id) on delete restrict,
  skill_source                public.skill_source not null,
  skill_combined_weight       numeric(5,4) not null check (skill_combined_weight >= 0 and skill_combined_weight <= 1),
  skill_required_level        smallint not null check (skill_required_level between 1 and 5),
  question_archetype          public.question_archetype not null,
  difficulty_asked            smallint not null check (difficulty_asked between 1 and 10),
  -- evidence weighting (§14.2, AI_Engine_Spec §2.9)
  evidence_weight             numeric(4,3) not null default 1.000 check (evidence_weight >= 0 and evidence_weight <= 1.2),   -- retention_check base is 1.2
  check_passed                boolean,
  familiarity                 public.familiarity,
  -- evaluator outputs (AI_Engine_Spec §2.3)
  correctness                 numeric(4,3) check (correctness between 0 and 1),
  depth                       numeric(4,3) check (depth between 0 and 1),
  clarity                     numeric(4,3) check (clarity between 0 and 1),
  structure                   numeric(4,3) check (structure between 0 and 1),
  tradeoff_reasoning          numeric(4,3) check (tradeoff_reasoning between 0 and 1),
  risk_awareness              numeric(4,3) check (risk_awareness between 0 and 1),
  hedging_ratio               numeric(4,3) check (hedging_ratio between 0 and 1),
  observed_skill_scores       jsonb,
  response_latency_ms         integer check (response_latency_ms >= 0),
  answer_duration_ms          integer check (answer_duration_ms >= 0),
  answer_length_tokens        integer check (answer_length_tokens >= 0),
  revision_count              integer check (revision_count >= 0),
  -- derived state
  knowledge_score_before      numeric(5,2) check (knowledge_score_before between 0 and 100),
  knowledge_score_after       numeric(5,2) check (knowledge_score_after between 0 and 100),
  confidence_score_before     numeric(5,2) check (confidence_score_before between 0 and 100),
  confidence_score_after      numeric(5,2) check (confidence_score_after between 0 and 100),
  provisional_level_after     smallint check (provisional_level_after between 1 and 5),
  -- adaptive decision
  decision_action             public.decision_action,
  decision_reason_code        varchar(60),
  difficulty_next             smallint check (difficulty_next between 1 and 10),
  skill_next_id               uuid references public.skill(id) on delete set null,
  subject_next_id             uuid references public.skill(id) on delete set null,
  subject_switch              boolean not null default false,
  hint_delivered              boolean not null default false,
  hint_level                  smallint not null default 0 check (hint_level between 0 and 3),
  hint_requested_by_user      boolean not null default false,
  tip_delivered_id            uuid references public.delivered_tip(id) on delete set null,
  struggle_budget_remaining   smallint,
  recovered_after_hint        boolean,
  -- provenance
  evaluator_model             varchar(80),
  evaluator_version           varchar(20),
  decision_engine_version     varchar(20),
  eval_latency_ms             integer check (eval_latency_ms >= 0),
  eval_flags                  text[] not null default '{}',
  b2b_eligible                boolean not null default false,
  created_at                  timestamptz not null default now(),

  -- a simulation row never carries an attempt_id; a practice row never carries a
  -- session_id or turn_id (container ids become NULL after ON DELETE SET NULL)
  constraint evaluation_metrics_container_chk check (
    (mode = 'simulation' and attempt_id is null) or
    (mode in ('quick', 'deep', 'diagnostic', 'retention_check') and turn_id is null and session_id is null)
  ),
  -- simulation rows always have their denormalized session context (spec NOT NULLs)
  constraint evaluation_metrics_session_context_chk check (
    mode <> 'simulation' or (
      role_template_id is not null and role_template_version is not null and company_profile_id is not null
      and turn_index is not null and family is not null and sub_family is not null and seniority is not null
    )
  )
);

comment on table  public.evaluation_metrics is 'Append-only evidence behind every skill assessment (Data_Models §9). One row per examined skill per turn or attempt. The Phase 2 data asset.';
comment on column public.evaluation_metrics.user_id is 'Not a foreign key on purpose: replaced with an anonymized hash when the user is deleted (Data_Models §18).';
comment on column public.evaluation_metrics.evidence_weight is 'Mode x familiarity x hint x exposure x reveal weight (AI_Engine_Spec §2.9). 0 when the reference was revealed before submitting.';

-- container lookups (partial: practice rows have no session/turn, simulation rows no attempt)
create index evaluation_metrics_session_turn_idx    on public.evaluation_metrics (session_id, turn_index) where session_id is not null;
create index evaluation_metrics_turn_idx            on public.evaluation_metrics (turn_id)          where turn_id is not null;          -- FK delete path
create index evaluation_metrics_attempt_idx         on public.evaluation_metrics (attempt_id)       where attempt_id is not null;
create index evaluation_metrics_tip_idx             on public.evaluation_metrics (tip_delivered_id) where tip_delivered_id is not null; -- FK delete path
-- per-user reads (profile roll-up, priors, RLS)
create index evaluation_metrics_user_skill_idx      on public.evaluation_metrics (user_id, skill_id, created_at);
create index evaluation_metrics_user_subject_idx    on public.evaluation_metrics (user_id, subject_id, created_at);
-- Phase 2 analytics (spec §9.2); cheap at pilot scale, rebuild CONCURRENTLY if they get in the way
create index evaluation_metrics_skill_difficulty_idx on public.evaluation_metrics (skill_id, difficulty_asked, created_at);
create index evaluation_metrics_company_skill_idx   on public.evaluation_metrics (company_profile_id, skill_id, b2b_eligible);
create index evaluation_metrics_decision_idx        on public.evaluation_metrics (decision_action, created_at);
-- time axis for append-only data: BRIN is ~1000x smaller than a btree here
create index evaluation_metrics_created_brin        on public.evaluation_metrics using brin (created_at) with (pages_per_range = 32);

-- append-only; recovered_after_hint is written once on the following turn (non-indexed, HOT)
alter table public.evaluation_metrics set (
  fillfactor = 95,
  autovacuum_vacuum_insert_scale_factor = 0.05,
  autovacuum_analyze_scale_factor = 0.02
);

create trigger evaluation_metrics_subject_is_domain
  before insert or update of subject_id on public.evaluation_metrics
  for each row execute function public.enforce_skill_node_type('subject_id', 'domain');

create trigger evaluation_metrics_skill_is_leaf
  before insert or update of skill_id on public.evaluation_metrics
  for each row execute function public.enforce_skill_node_type('skill_id', 'skill');

create trigger evaluation_metrics_skill_next_is_leaf
  before insert or update of skill_next_id on public.evaluation_metrics
  for each row execute function public.enforce_skill_node_type('skill_next_id', 'skill');

create trigger evaluation_metrics_subject_next_is_domain
  before insert or update of subject_next_id on public.evaluation_metrics
  for each row execute function public.enforce_skill_node_type('subject_next_id', 'domain');

-- §7.1  User_Skill_Assessment: one row per planned skill per session, written at session end
create table public.user_skill_assessment (
  id                     uuid primary key default gen_random_uuid(),
  session_id             uuid not null references public.interview_session(id) on delete cascade,
  user_id                uuid not null references public.user_profile(id) on delete cascade,
  skill_id               uuid not null references public.skill(id) on delete restrict,
  source                 public.skill_source not null,
  assessment_mode        public.assessment_mode not null,
  status                 public.assessment_status not null,
  turns_count            smallint not null default 0 check (turns_count >= 0),
  knowledge_score        numeric(5,2) check (knowledge_score between 0 and 100),
  confidence_score       numeric(5,2) check (confidence_score between 0 and 100),
  demonstrated_ceiling   smallint check (demonstrated_ceiling between 1 and 10),
  proficiency_level      smallint check (proficiency_level between 1 and 5),
  required_level         smallint not null check (required_level between 1 and 5),
  level_gap              smallint generated always as (proficiency_level - required_level) stored,
  meets_requirement      boolean  generated always as (proficiency_level >= required_level) stored,
  hints_used             smallint not null default 0 check (hints_used >= 0),
  evidence_turn_ids      uuid[] not null default '{}',
  strengths              text[] not null default '{}',
  gaps                   text[] not null default '{}',
  evaluator_version      varchar(20),
  created_at             timestamptz not null default now(),

  constraint user_skill_assessment_unique unique (session_id, skill_id),
  -- never report a level without evidence (core decision 3): assessed rows have a
  -- level, not_assessed rows have none, insufficient_evidence rows may carry a
  -- provisional level (AI_Engine_Spec §2.6: "shown with a provisional label")
  constraint user_skill_assessment_level_by_status_chk check (
    (status <> 'assessed' or proficiency_level is not null) and
    (status <> 'not_assessed' or proficiency_level is null)
  )
);

comment on table public.user_skill_assessment is 'How the user scored on each skill in one session (Data_Models §7.1). Evidence rules in AI_Engine_Spec §2.6.';

create index user_skill_assessment_user_skill_idx on public.user_skill_assessment (user_id, skill_id, created_at desc);

create trigger user_skill_assessment_skill_is_leaf
  before insert or update of skill_id on public.user_skill_assessment
  for each row execute function public.enforce_skill_node_type('skill_id', 'skill');

-- §7.2  Skill_Set_Scorecard: role fit, company fit, overall; three per session
create table public.skill_set_scorecard (
  id                            uuid primary key default gen_random_uuid(),
  session_id                    uuid not null references public.interview_session(id) on delete cascade,
  user_id                       uuid not null references public.user_profile(id) on delete cascade,
  scope                         public.scorecard_scope not null,
  fit_score                     numeric(5,2) check (fit_score between 0 and 100),
  skills_total                  smallint not null default 0 check (skills_total >= 0),
  skills_assessed               smallint not null default 0 check (skills_assessed >= 0),
  skills_meeting_requirement    smallint not null default 0 check (skills_meeting_requirement >= 0),
  core_gaps                     uuid[] not null default '{}',
  top_strengths                 uuid[] not null default '{}',
  domain_breakdown              jsonb,
  created_at                    timestamptz not null default now(),

  constraint skill_set_scorecard_unique unique (session_id, scope),
  constraint skill_set_scorecard_counts_chk check (
    skills_assessed <= skills_total and skills_meeting_requirement <= skills_assessed
  )
);

comment on table  public.skill_set_scorecard is 'Fit of the user against a whole skill set in one session (Data_Models §7.2). Core-gap caps: 60% at two levels below, 80% at one level below.';
comment on column public.skill_set_scorecard.domain_breakdown is 'Fit score per domain, for report charts.';

-- §7.3  User_Skill_Profile: running level per skill across all sessions
create table public.user_skill_profile (
  id                     uuid primary key default gen_random_uuid(),
  user_id                uuid not null references public.user_profile(id) on delete cascade,
  skill_id               uuid not null references public.skill(id) on delete restrict,
  proficiency_level      smallint check (proficiency_level between 1 and 5),
  level_score            numeric(4,2) check (level_score between 1 and 5),
  knowledge_score        numeric(5,2) check (knowledge_score between 0 and 100),
  confidence_score       numeric(5,2) check (confidence_score between 0 and 100),
  assessments_count      smallint not null default 0 check (assessments_count >= 0),
  evidence_turns_total   integer not null default 0 check (evidence_turns_total >= 0),
  trend                  public.skill_trend not null default 'new',
  level_history          jsonb not null default '[]'::jsonb,
  first_assessed_at      timestamptz,
  last_assessed_at       timestamptz,
  -- spaced retention checks (AI_Engine_Spec §4.11): 3-5 days after a level rises, then 10-14 days
  retention_due_at         date,
  retention_checks_passed  smallint not null default 0 check (retention_checks_passed >= 0),
  last_retention_check_at  timestamptz,
  updated_at             timestamptz not null default now(),

  constraint user_skill_profile_unique unique (user_id, skill_id),
  constraint user_skill_profile_history_array_chk check (jsonb_typeof(level_history) = 'array')
);

comment on table  public.user_skill_profile is 'Current best estimate per skill across sessions (Data_Models §7.3). Roll-up rule: recency- and evidence-weighted.';
comment on column public.user_skill_profile.level_history is '[{"session_id": "...", "level": 3, "at": "..."}]';
comment on column public.user_skill_profile.retention_due_at is 'Next scheduled retention check on an unfamiliar question in this skill; null when none is due.';

create index user_skill_profile_skill_idx         on public.user_skill_profile (skill_id);
-- daily Plan Router job: "all retention checks due by today" across users
create index user_skill_profile_retention_due_idx on public.user_skill_profile (retention_due_at, user_id) where retention_due_at is not null;

create trigger user_skill_profile_set_updated_at
  before update on public.user_skill_profile
  for each row execute function public.set_updated_at();

create trigger user_skill_profile_skill_is_leaf
  before insert or update of skill_id on public.user_skill_profile
  for each row execute function public.enforce_skill_node_type('skill_id', 'skill');

-- §8.4  Session_Report
create table public.session_report (
  id                         uuid primary key default gen_random_uuid(),
  session_id                 uuid not null unique references public.interview_session(id) on delete cascade,
  role_scorecard_id          uuid references public.skill_set_scorecard(id) on delete set null,
  company_scorecard_id       uuid references public.skill_set_scorecard(id) on delete set null,   -- null for Generic
  overall_scorecard_id       uuid references public.skill_set_scorecard(id) on delete set null,
  difficulty_timeline        jsonb,
  top_tips                   jsonb,
  narrative_md               text,
  recommended_next_skills    uuid[] not null default '{}',
  generated_at               timestamptz not null default now(),
  generation_meta            jsonb
);

comment on table  public.session_report is 'Post-session report (Data_Models §8.4). narrative_md is LLM-generated at high effort.';
comment on column public.session_report.difficulty_timeline is '[{"turn": 0, "skill_key": "...", "difficulty": 4, "action": "ESCALATE"}, ...]';

-- FK delete paths (scorecards cascade with the session)
create index session_report_role_sc_idx    on public.session_report (role_scorecard_id)    where role_scorecard_id is not null;
create index session_report_company_sc_idx on public.session_report (company_scorecard_id) where company_scorecard_id is not null;
create index session_report_overall_sc_idx on public.session_report (overall_scorecard_id) where overall_scorecard_id is not null;

-- ---- §18  Anonymize evaluation_metrics when a user is deleted ------------------
-- Fires on soft delete (deleted_at set) and on hard delete, including the cascade
-- from auth.users. SECURITY DEFINER because the cascade may run as the auth
-- service role, which has no privileges on evaluation_metrics. The replacement
-- user_id is a deterministic hash of the real id, so rows from one deleted user
-- still group together for aggregate statistics without linking back to a person.
create or replace function public.anonymize_user_metrics()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if tg_op = 'DELETE' or (new.deleted_at is not null and old.deleted_at is null) then
    update public.evaluation_metrics
       set user_id       = md5('anon:' || old.id::text)::uuid,
           anonymized_at = now(),
           b2b_eligible  = false
     where user_id = old.id
       and anonymized_at is null;
  end if;
  return coalesce(new, old);
end;
$$;

revoke execute on function public.anonymize_user_metrics() from public, anon, authenticated;

create trigger user_profile_anonymize_metrics
  before update of deleted_at or delete on public.user_profile
  for each row execute function public.anonymize_user_metrics();
