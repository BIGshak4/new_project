-- ============================================================================
-- 0400  Roles and companies
-- Source: src/Data_Models.md §4 (Role_Template, Role_Skill_Set),
--         §5 (Company_Profile, Company_Skill_Set), §16 (Company_Evidence)
-- ============================================================================

-- §4.1  Role_Template
create table public.role_template (
  id                    uuid primary key default gen_random_uuid(),
  slug                  varchar(80)  not null unique,
  title                 varchar(160) not null,
  family                public.role_family not null,
  sub_family            varchar(60)  not null,
  description           text,
  origin                public.role_origin not null default 'system',
  owner_user_id         uuid references public.user_profile(id) on delete set null,
  seniority_profiles    jsonb not null,
  question_archetypes   jsonb,
  is_active             boolean not null default true,
  version               integer not null default 1,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now(),

  constraint role_template_seniority_profiles_chk check (jsonb_typeof(seniority_profiles) = 'object'),
  constraint role_template_archetypes_chk         check (question_archetypes is null or jsonb_typeof(question_archetypes) = 'object'),
  -- system roles never have an owner. A user_derived role keeps its owner until
  -- that user is deleted (ON DELETE SET NULL), after which it is orphaned.
  constraint role_template_owner_by_origin_chk check (
    origin = 'user_derived' or owner_user_id is null
  )
);

comment on table  public.role_template is 'A role is a list of catalog skills with weights and required levels per seniority (Data_Models §4.1).';
comment on column public.role_template.seniority_profiles is '{"student": {"baseline_difficulty": 1, "difficulty_ceiling": 5}, "junior": {...}, ...}';

create index role_template_family_active_idx on public.role_template (family, is_active);
create index role_template_owner_idx         on public.role_template (owner_user_id) where owner_user_id is not null;

create trigger role_template_set_updated_at
  before update on public.role_template
  for each row execute function public.set_updated_at();

-- §4.2  Role_Skill_Set: one row per role version per skill
create table public.role_skill_set (
  id                     uuid primary key default gen_random_uuid(),
  role_template_id       uuid not null references public.role_template(id) on delete cascade,
  role_template_version  integer not null,
  skill_id               uuid not null references public.skill(id) on delete restrict,
  weight                 numeric(5,4) not null check (weight >= 0 and weight <= 1),
  importance             public.importance not null,
  required_level         jsonb not null,
  assessment_mode        public.assessment_mode,            -- null = use the skill's default
  difficulty_override    int4range,                         -- narrows the skill's range for this role
  evaluation_notes       text,

  constraint role_skill_set_unique          unique (role_template_id, role_template_version, skill_id),
  constraint role_skill_set_required_level_chk  check (jsonb_typeof(required_level) = 'object'),
  constraint role_skill_set_difficulty_override_chk check (
    difficulty_override is null or
    (not isempty(difficulty_override) and difficulty_override <@ int4range(1, 11))
  )
);

comment on column public.role_skill_set.required_level is 'Required proficiency per seniority, e.g. {"student": 2, "junior": 2, "mid": 3, ...}. Values 1-5; validated by the seed loader.';
comment on column public.role_skill_set.difficulty_override is 'Optional sub-range of 1..10 for this role. Stored as int4range with inclusive lower bound.';

create index role_skill_set_skill_idx on public.role_skill_set (skill_id);

create trigger role_skill_set_skill_is_leaf
  before insert or update of skill_id on public.role_skill_set
  for each row execute function public.enforce_skill_node_type('skill_id', 'skill');

-- §5.1  Company_Profile (+ §16 evidence counters)
create table public.company_profile (
  id                     uuid primary key default gen_random_uuid(),
  slug                   varchar(80)  not null unique,
  display_name           varchar(160) not null,
  industry               varchar(80),
  core_values            jsonb not null default '[]'::jsonb,
  risk_tolerance         smallint check (risk_tolerance between 1 and 10),
  interview_style        jsonb not null default '{}'::jsonb,
  company_weight_share   numeric(3,2) not null default 0.30 check (company_weight_share between 0 and 1),
  culture_prompt_block   text not null default '',
  is_public              boolean not null default true,
  version                integer not null default 1,
  evidence_count         integer not null default 0 check (evidence_count >= 0),
  evidence_latest_at     date,
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now(),

  constraint company_profile_core_values_chk     check (jsonb_typeof(core_values) = 'array'),
  constraint company_profile_interview_style_chk check (jsonb_typeof(interview_style) = 'object')
);

comment on table  public.company_profile is 'Company culture and interview style (Data_Models §5.1). The Generic profile has company_weight_share = 0 and no skill rows.';
comment on column public.company_profile.evidence_count is 'Shown as "based on N dated sources, latest {evidence_latest_at}" (Data_Models §16).';

create trigger company_profile_set_updated_at
  before update on public.company_profile
  for each row execute function public.set_updated_at();

-- §16.1  Company_Evidence: every company claim traces to a dated record
create table public.company_evidence (
  id                    uuid primary key default gen_random_uuid(),
  company_profile_id    uuid not null references public.company_profile(id) on delete cascade,
  source_type           public.evidence_source_type not null,
  role_scope            varchar(120),
  seniority_scope       varchar(40),
  site                  varchar(80),
  observed_at           date not null,
  source_url            varchar(512),
  summary               text not null,
  confidence            public.evidence_confidence not null,
  supports_skill_ids    uuid[] not null default '{}',
  supports_style_keys   text[] not null default '{}',
  added_by              varchar(120),
  created_at            timestamptz not null default now()
);

comment on table public.company_evidence is 'Dated evidence behind company claims (Data_Models §16.1). A single candidate_report never makes a skill core. Confidential employer material is never stored.';

create index company_evidence_company_idx on public.company_evidence (company_profile_id, observed_at desc);

-- §5.2  Company_Skill_Set
create table public.company_skill_set (
  id                        uuid primary key default gen_random_uuid(),
  company_profile_id        uuid not null references public.company_profile(id) on delete cascade,
  company_profile_version   integer not null,
  skill_id                  uuid not null references public.skill(id) on delete restrict,
  scope                     public.company_scope not null,
  scope_family              public.skill_family,
  scope_role_template_id    uuid references public.role_template(id) on delete cascade,
  weight                    numeric(5,4) not null check (weight >= 0 and weight <= 1),
  importance                public.importance not null,
  required_level_offset     smallint not null default 0 check (required_level_offset between -4 and 4),
  required_level_min        smallint check (required_level_min between 1 and 5),
  assessment_mode           public.assessment_mode,        -- null = use the skill's default
  examination_notes         text,
  evidence_ids              uuid[] not null default '{}',

  constraint company_skill_set_unique unique nulls not distinct
    (company_profile_id, company_profile_version, skill_id, scope, scope_family, scope_role_template_id),
  constraint company_skill_set_scope_family_chk check (scope_family is null or scope_family in ('hardware', 'software')),
  constraint company_skill_set_scope_shape_chk check (
    (scope = 'all_roles' and scope_family is null     and scope_role_template_id is null) or
    (scope = 'family'    and scope_family is not null and scope_role_template_id is null) or
    (scope = 'role'      and scope_family is null     and scope_role_template_id is not null)
  )
);

comment on column public.company_skill_set.evidence_ids is 'company_evidence ids supporting this row. A row with no evidence cannot be published; enforced by the seed loader and content pipeline (Data_Models §16).';

create index company_skill_set_skill_idx on public.company_skill_set (skill_id);
create index company_skill_set_role_idx  on public.company_skill_set (scope_role_template_id) where scope_role_template_id is not null;

create trigger company_skill_set_skill_is_leaf
  before insert or update of skill_id on public.company_skill_set
  for each row execute function public.enforce_skill_node_type('skill_id', 'skill');
