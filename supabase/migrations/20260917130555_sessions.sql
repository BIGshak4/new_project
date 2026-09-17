-- ============================================================================
-- 0700  Sessions and practice
-- Source: src/Data_Models.md §6 (Interview_Session, Session_Skill_Plan,
--         Session_Turn), §14.2 (Attempt), §8.3 (Delivered_Tip), §8.5 (User_Document)
-- ============================================================================

-- §6.1  Interview_Session (simulation mode). Live state is the JSONB `state` column in the MVP (§10).
create table public.interview_session (
  id                        uuid primary key default gen_random_uuid(),
  user_id                   uuid not null references public.user_profile(id) on delete cascade,
  role_template_id          uuid not null references public.role_template(id) on delete restrict,
  role_template_version     integer not null,
  company_profile_id        uuid not null references public.company_profile(id) on delete restrict,
  company_profile_version   integer not null,
  seniority                 public.seniority not null,
  baseline_difficulty       smallint not null check (baseline_difficulty between 1 and 10),
  difficulty_ceiling        smallint not null check (difficulty_ceiling between 1 and 10),
  status                    public.session_status not null default 'configured',
  config                    jsonb not null default '{}'::jsonb,
  state                     jsonb,
  turn_count                integer not null default 0 check (turn_count >= 0),
  hints_used                integer not null default 0 check (hints_used >= 0),
  hints_requested_by_user   integer not null default 0 check (hints_requested_by_user >= 0),
  b2b_eligible              boolean not null default false,
  started_at                timestamptz,
  ended_at                  timestamptz,
  created_at                timestamptz not null default now(),

  constraint interview_session_difficulty_chk  check (baseline_difficulty <= difficulty_ceiling),
  constraint interview_session_config_chk      check (jsonb_typeof(config) = 'object'),
  constraint interview_session_timeline_chk    check (ended_at is null or started_at is null or ended_at >= started_at)
);

comment on table  public.interview_session is 'One interview simulation (Data_Models §6.1). Role and company versions are pinned at start.';
comment on column public.interview_session.config is '{"planned_duration_min": 45, "focus_skill_keys": [...], "coach_mode": true, "struggle_budget_per_skill": 2}';
comment on column public.interview_session.state  is 'Live session state (Data_Models §10). Moves to Redis in the target architecture.';

create index interview_session_user_created_idx on public.interview_session (user_id, created_at desc);
create index interview_session_role_status_idx  on public.interview_session (role_template_id, status);
create index interview_session_b2b_idx          on public.interview_session (ended_at) where b2b_eligible;
-- "resume my open session" on app open
create index interview_session_open_idx         on public.interview_session (user_id) where status in ('configured', 'in_progress', 'paused');

-- state (2-5 KB JSONB) and the counters are rewritten every turn; none are indexed,
-- so updates stay HOT if the page has free space
alter table public.interview_session set (fillfactor = 70);

-- §6.2  Session_Skill_Plan: merged skill set, frozen at session start
create table public.session_skill_plan (
  id                  uuid primary key default gen_random_uuid(),
  session_id          uuid not null references public.interview_session(id) on delete cascade,
  skill_id            uuid not null references public.skill(id) on delete restrict,
  source              public.skill_source not null,
  role_weight         numeric(5,4) not null default 0 check (role_weight >= 0 and role_weight <= 1),
  company_weight      numeric(5,4) not null default 0 check (company_weight >= 0 and company_weight <= 1),
  combined_weight     numeric(5,4) not null check (combined_weight >= 0 and combined_weight <= 1),
  importance          public.importance not null,
  required_level      smallint not null check (required_level between 1 and 5),
  assessment_mode     public.assessment_mode not null,
  planned_turns       smallint not null default 0 check (planned_turns >= 0),
  priority_rank       smallint,
  examination_notes   text,

  constraint session_skill_plan_unique unique (session_id, skill_id),
  -- observed skills never get their own question turns
  constraint session_skill_plan_observed_turns_chk check (assessment_mode <> 'observed' or planned_turns = 0)
);

comment on table public.session_skill_plan is 'Which skills this session examines, why, and with how much time (Data_Models §6.2, merge algorithm §6.3).';

create trigger session_skill_plan_skill_is_leaf
  before insert or update of skill_id on public.session_skill_plan
  for each row execute function public.enforce_skill_node_type('skill_id', 'skill');

-- §6.4  Session_Turn: one question and answer in a simulation
create table public.session_turn (
  id                          uuid primary key default gen_random_uuid(),
  session_id                  uuid not null references public.interview_session(id) on delete cascade,
  turn_index                  integer not null check (turn_index >= 0),
  skill_id                    uuid not null references public.skill(id) on delete restrict,
  question_id                 uuid references public.question(id) on delete set null,   -- set when a bank question was used (§13: bank first)
  question_archetype          public.question_archetype not null,
  difficulty                  smallint not null check (difficulty between 1 and 10),
  question_text               text not null,
  expected_answer_outline     text,                                                     -- private: evaluator only
  question_generation_meta    jsonb,
  answer_text                 text,
  answer_code                 text,
  answer_language             varchar(40),
  check_result                jsonb,                                                    -- deterministic check output (§13.4)
  answer_started_at           timestamptz,
  answer_submitted_at         timestamptz,
  created_at                  timestamptz not null default now(),

  constraint session_turn_unique unique (session_id, turn_index)
);

comment on table  public.session_turn is 'Simulation transcript, one row per turn (Data_Models §6.4). Retained 24 months, hard-deleted with the user (§18).';
comment on column public.session_turn.expected_answer_outline is 'Private. Never exposed to the client (column-level grant removed in 1000_rls.sql).';

create index session_turn_skill_idx    on public.session_turn (skill_id);
create index session_turn_question_idx on public.session_turn (question_id) where question_id is not null;

-- one update per row (answer submit), append-heavy
alter table public.session_turn set (fillfactor = 90, autovacuum_analyze_scale_factor = 0.02);

create trigger session_turn_skill_is_leaf
  before insert or update of skill_id on public.session_turn
  for each row execute function public.enforce_skill_node_type('skill_id', 'skill');

-- §14.2  Attempt: one quick-practice item or one deep-practice question with follow-ups
create table public.attempt (
  id                        uuid primary key default gen_random_uuid(),
  user_id                   uuid not null references public.user_profile(id) on delete cascade,
  question_id               uuid not null references public.question(id) on delete restrict,
  question_version          integer not null,
  mode                      public.practice_mode not null,
  plan_item_id              uuid,                              -- FK added in 0900 (plan_item is created there)
  practice_language         public.content_language not null,
  self_confidence_before    smallint check (self_confidence_before between 1 and 5),
  answer                    jsonb,
  check_result              jsonb,
  evaluation                jsonb,
  band                      public.answer_band,
  hints_used                smallint not null default 0 check (hints_used >= 0),   -- total across the question and its follow-ups
  reference_revealed        boolean not null default false,
  revealed_before_submit    boolean not null default false,
  follow_up_turns           jsonb not null default '[]'::jsonb,
  misconceptions_hit        text[] not null default '{}',
  familiarity               public.familiarity not null default 'new',
  duration_ms               integer check (duration_ms >= 0),
  started_at                timestamptz not null default now(),
  submitted_at              timestamptz,
  evaluator_version         varchar(20),

  constraint attempt_mode_chk              check (mode in ('quick', 'deep')),
  constraint attempt_follow_ups_array_chk  check (jsonb_typeof(follow_up_turns) = 'array'),
  -- revealing the reference before submitting implies it was revealed
  constraint attempt_reveal_chk            check (revealed_before_submit = false or reference_revealed = true),
  -- a band implies a submission (the reverse is not required: the evaluator may fail
  -- after submission, and the attempt still counts for the streak)
  constraint attempt_band_requires_submit_chk check (band is null or submitted_at is not null)
);

comment on table  public.attempt is 'Quick and deep practice (Data_Models §14.2). Simulation uses interview_session instead.';
comment on column public.attempt.revealed_before_submit is 'If true, evidence weight is 0 for this attempt (AI_Engine_Spec §2.9).';
comment on column public.attempt.follow_up_turns is 'Deep practice: [{"question": ..., "answer": ..., "evaluation": ..., "generated": true}]';

create index attempt_user_submitted_idx  on public.attempt (user_id, submitted_at desc);
create index attempt_question_band_idx   on public.attempt (question_id, band);
create index attempt_plan_item_idx       on public.attempt (plan_item_id) where plan_item_id is not null;
-- familiarity check in bank-first selection: "which questions has this user attempted"
create index attempt_user_question_idx   on public.attempt (user_id, question_id);

-- start -> hints -> submit -> follow-ups: several updates per row
alter table public.attempt set (fillfactor = 85, autovacuum_analyze_scale_factor = 0.02);

-- §8.3  Delivered_Tip: a tip instance shown during a session or after a deep-practice attempt
create table public.delivered_tip (
  id                          uuid primary key default gen_random_uuid(),
  session_id                  uuid references public.interview_session(id) on delete cascade,
  turn_id                     uuid references public.session_turn(id) on delete cascade,   -- null for post-session
  attempt_id                  uuid references public.attempt(id) on delete cascade,        -- deep practice tips
  tip_id                      uuid not null references public.tips_library(id) on delete restrict,
  skill_id                    uuid references public.skill(id) on delete set null,
  rendered_text               text not null,
  timing                      public.tip_delivery_timing not null,
  was_requested               boolean not null default false,
  candidate_rating            smallint check (candidate_rating between 1 and 5),
  behavior_improved_next_n    boolean,
  delivered_at                timestamptz not null default now(),

  constraint delivered_tip_timing_chk   check (timing <> 'both'),
  constraint delivered_tip_container_chk check (session_id is not null or attempt_id is not null)
);

comment on table public.delivered_tip is 'A rendered tip shown to the user (Data_Models §8.3). Belongs to a session or to a deep-practice attempt.';

create index delivered_tip_session_idx on public.delivered_tip (session_id) where session_id is not null;
create index delivered_tip_turn_idx    on public.delivered_tip (turn_id)    where turn_id is not null;      -- FK delete path
create index delivered_tip_attempt_idx on public.delivered_tip (attempt_id) where attempt_id is not null;
create index delivered_tip_tip_idx     on public.delivered_tip (tip_id);

create trigger delivered_tip_skill_is_leaf
  before insert or update of skill_id on public.delivered_tip
  for each row execute function public.enforce_skill_node_type('skill_id', 'skill');

-- §8.5  User_Document (resume / job description upload; not in the beta UI, table kept for the roadmap)
create table public.user_document (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references public.user_profile(id) on delete cascade,
  doc_type         public.document_type not null,
  storage_key      varchar(512) not null,
  parsed_payload   jsonb,
  parse_status     public.parse_status not null default 'pending',
  uploaded_at      timestamptz not null default now()
);

comment on table public.user_document is 'Uploaded documents (Data_Models §8.5). parsed_payload is PII-stripped.';

create index user_document_user_idx on public.user_document (user_id, uploaded_at desc);
