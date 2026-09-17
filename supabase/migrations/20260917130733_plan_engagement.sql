-- ============================================================================
-- 0900  Learning plan and daily loop
-- Source: src/Data_Models.md §15 (Learning_Plan, Plan_Item, Daily_Challenge,
--         User_Engagement, Notification)
-- Also closes two forward references: attempt.plan_item_id and learning_plan.next_item_id.
-- ============================================================================

-- §15.1  Learning_Plan: one active plan per user, regenerated weekly
create table public.learning_plan (
  id                       uuid primary key default gen_random_uuid(),
  user_id                  uuid not null references public.user_profile(id) on delete cascade,
  target_role_id           uuid not null references public.role_template(id) on delete restrict,
  target_company_id        uuid references public.company_profile(id) on delete set null,
  seniority                public.seniority not null,
  target_interview_date    date,
  week_start               date not null,
  minutes_per_day          smallint check (minutes_per_day between 1 and 720),
  focus_skill_ids          uuid[] not null default '{}',
  retention_skill_ids      uuid[] not null default '{}',
  unassessed_skill_ids     uuid[] not null default '{}',
  next_item_id             uuid,                         -- FK added below, after plan_item exists
  is_active                boolean not null default true,
  generated_at             timestamptz not null default now(),
  router_version           varchar(20)
);

comment on table  public.learning_plan is 'Weekly plan produced by the Plan Router (Data_Models §15.1, AI_Engine_Spec §4.11). One active plan per user.';
comment on column public.learning_plan.retention_skill_ids is 'Skills due for a spaced retention check, 3 to 5 days after a level rises.';

create unique index learning_plan_one_active_idx on public.learning_plan (user_id) where is_active;
create index learning_plan_user_idx on public.learning_plan (user_id, generated_at desc);

-- §15.2  Plan_Item
create table public.plan_item (
  id                       uuid primary key default gen_random_uuid(),
  plan_id                  uuid not null references public.learning_plan(id) on delete cascade,
  day_index                smallint not null check (day_index between 0 and 6),
  mode                     public.activity_mode not null,
  skill_ids                uuid[] not null default '{}',
  question_id              uuid references public.question(id) on delete set null,     -- chosen at start time if null
  reason                   text not null,
  estimated_minutes        smallint check (estimated_minutes between 1 and 120),
  status                   public.plan_item_status not null default 'planned',
  completed_attempt_id     uuid references public.attempt(id) on delete set null,
  completed_session_id     uuid references public.interview_session(id) on delete set null,
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);

comment on table  public.plan_item is 'One recommended activity in a plan (Data_Models §15.2). reason is shown to the user in plain language.';

create index plan_item_plan_day_idx           on public.plan_item (plan_id, day_index);
create index plan_item_completed_attempt_idx  on public.plan_item (completed_attempt_id) where completed_attempt_id is not null;  -- FK delete path
create index plan_item_completed_session_idx  on public.plan_item (completed_session_id) where completed_session_id is not null;  -- FK delete path

create trigger plan_item_set_updated_at
  before update on public.plan_item
  for each row execute function public.set_updated_at();

-- close the forward references
alter table public.learning_plan
  add constraint learning_plan_next_item_fk
  foreign key (next_item_id) references public.plan_item(id) on delete set null;

alter table public.attempt
  add constraint attempt_plan_item_fk
  foreign key (plan_item_id) references public.plan_item(id) on delete set null;

-- §15.3  Daily_Challenge: one quick question per day per language
create table public.daily_challenge (
  id              uuid primary key default gen_random_uuid(),
  date            date not null,
  language        public.content_language not null,
  question_id     uuid not null references public.question(id) on delete restrict,
  participants    integer not null default 0 check (participants >= 0),
  success_rate    numeric(4,3) check (success_rate between 0 and 1),
  created_at      timestamptz not null default now(),

  constraint daily_challenge_unique unique (date, language)
);

comment on table public.daily_challenge is 'Daily challenge (Data_Models §15.3): quick format, medium difficulty, broad subject. success_rate shown after the user answers.';

-- §15.4  User_Engagement: points, streaks, goals. Never feeds the skill profile.
create table public.user_engagement (
  user_id                 uuid primary key references public.user_profile(id) on delete cascade,
  points                  integer  not null default 0 check (points >= 0),
  streak_days             smallint not null default 0 check (streak_days >= 0),
  streak_last_date        date,
  weekly_goal_minutes     smallint check (weekly_goal_minutes between 0 and 5040),
  weekly_minutes_done     smallint not null default 0 check (weekly_minutes_done >= 0),
  achievements            jsonb not null default '[]'::jsonb,
  updated_at              timestamptz not null default now(),

  constraint user_engagement_achievements_array_chk check (jsonb_typeof(achievements) = 'array')
);

comment on table public.user_engagement is 'Participation, consistency and improvement rewards (Data_Models §15.4). Never feeds scorecards.';

create trigger user_engagement_set_updated_at
  before update on public.user_engagement
  for each row execute function public.set_updated_at();

-- §15.5  Notification: one channel in the pilot
create table public.notification (
  id                 uuid primary key default gen_random_uuid(),
  user_id            uuid not null references public.user_profile(id) on delete cascade,
  channel            public.notification_channel not null,
  template_key       varchar(80) not null,
  personalization    jsonb not null default '{}'::jsonb,
  scheduled_for      timestamptz not null,
  sent_at            timestamptz,
  opened_at          timestamptz,
  created_at         timestamptz not null default now(),

  constraint notification_personalization_object_chk check (jsonb_typeof(personalization) = 'object')
);

comment on table  public.notification is 'Scheduled reminders (Data_Models §15.5). scheduled_for respects quiet hours and frequency from user_profile.notification_prefs.';
comment on column public.notification.personalization is 'Only facts from real history; empty when evidence is thin.';

create index notification_user_idx    on public.notification (user_id, scheduled_for desc);
create index notification_pending_idx on public.notification (scheduled_for) where sent_at is null;

-- ---- Per-action cost metering (System_Architecture §7.3, MVP_Build_Guide §7.6, §11) ----
-- Every LLM call, deterministic check and notification writes one row. A daily
-- roll-up per user and per mode drives the pilot limits and the allowance shown
-- in the UI. user_id is ON DELETE SET NULL so cost history survives deletion.
create table public.usage_event (
  id                    uuid primary key default gen_random_uuid(),
  user_id               uuid references public.user_profile(id) on delete set null,
  mode                  public.activity_mode,
  action                varchar(40) not null,      -- evaluate | generate | tip | report | check | notification | translate | other
  session_id            uuid references public.interview_session(id) on delete set null,
  attempt_id            uuid references public.attempt(id) on delete set null,
  model                 varchar(80),
  tokens_in             integer not null default 0 check (tokens_in >= 0),
  tokens_out            integer not null default 0 check (tokens_out >= 0),
  cache_read_tokens     integer not null default 0 check (cache_read_tokens >= 0),
  cache_write_tokens    integer not null default 0 check (cache_write_tokens >= 0),
  check_runtime_ms      integer check (check_runtime_ms >= 0),
  cost_usd              numeric(10,6) not null default 0 check (cost_usd >= 0),
  latency_ms            integer check (latency_ms >= 0),
  meta                  jsonb,
  created_at            timestamptz not null default now()
);

comment on table public.usage_event is 'One row per LLM call, deterministic check or notification (System_Architecture §7.3). Rolled up daily per user and mode for limits and pricing.';

-- per-request allowance check: count this user's events since the start of the day
-- (write the predicate as created_at >= $day_start, not date(created_at) = ..., so the index is used)
create index usage_event_user_created_idx on public.usage_event (user_id, created_at desc);
create index usage_event_session_idx      on public.usage_event (session_id) where session_id is not null;   -- FK delete path
create index usage_event_attempt_idx      on public.usage_event (attempt_id) where attempt_id is not null;   -- FK delete path
-- daily roll-up job scans one day range; append-only, so BRIN
create index usage_event_created_brin     on public.usage_event using brin (created_at) with (pages_per_range = 32);

alter table public.usage_event set (
  autovacuum_vacuum_insert_scale_factor = 0.05,
  autovacuum_analyze_scale_factor = 0.02
);
