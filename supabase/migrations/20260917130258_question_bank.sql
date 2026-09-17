-- ============================================================================
-- 0500  Question bank, translations, glossary
-- Source: src/Data_Models.md §13 (Question, Question_Skill, Question_Translation,
--         deterministic checks), §17 (Term_Glossary)
--
-- Language-neutral content (rubric, checks, assets, provenance) lives on
-- `question`. The prompt text for each language lives on `question_translation`,
-- and a question is served in a language only when parity_checked is true.
-- ============================================================================

-- §13.1  Question
create table public.question (
  id                    uuid primary key default gen_random_uuid(),
  key                   varchar(80) not null unique,
  status                public.question_status not null default 'draft',
  origin                public.question_origin not null,
  variation_of_id       uuid references public.question(id) on delete set null,
  format                public.question_format not null,
  practice_modes        public.practice_mode[] not null,
  subject_id            uuid not null references public.skill(id) on delete restrict,
  difficulty            smallint not null check (difficulty between 1 and 10),
  estimated_minutes     smallint check (estimated_minutes > 0),
  requirements          text  not null,
  accepted_approaches   jsonb,
  reference_solution    text  not null,
  hints                 jsonb not null default '[]'::jsonb,
  common_errors         jsonb,
  rubric                jsonb not null,
  deterministic_check   jsonb,
  choices               jsonb,
  assets                jsonb,
  source_name           varchar(160),
  source_url            varchar(512),
  license               varchar(80),
  reuse_status          public.reuse_status not null default 'pending_review',
  attribution_text      text,
  reviewed_by           varchar(120),
  reviewed_at           timestamptz,
  review_notes          text,
  times_served          integer not null default 0 check (times_served >= 0),
  exposure_risk         public.exposure_risk not null default 'low',
  version               integer not null default 1,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now(),

  constraint question_hints_is_array_chk    check (jsonb_typeof(hints) = 'array'),
  constraint question_rubric_is_object_chk  check (jsonb_typeof(rubric) = 'object'),
  constraint question_check_type_chk        check (
    deterministic_check is null or (
      jsonb_typeof(deterministic_check) = 'object' and
      deterministic_check ->> 'type' in ('truth_table', 'numeric', 'sim') and
      deterministic_check ? 'spec'
    )
  ),
  constraint question_not_own_variation_chk check (variation_of_id is null or variation_of_id <> id),
  -- Publication rules (Data_Models §13.1). Drafts may be incomplete; a published
  -- question must have at least one practice mode, choices if multiple choice,
  -- permitted reuse, and a reviewer (which also covers "ai_generated is never
  -- published without review").
  constraint question_publish_modes_chk     check (status <> 'published' or cardinality(practice_modes) >= 1),
  constraint question_publish_choices_chk   check (status <> 'published' or format <> 'multiple_choice' or choices is not null),
  constraint question_publish_reuse_chk     check (status <> 'published' or reuse_status in ('permitted', 'attribution_required')),
  constraint question_publish_reviewed_chk  check (status <> 'published' or (reviewed_by is not null and reviewed_at is not null))
);

comment on table  public.question is 'Reviewed question bank (Data_Models §13.1). Only published rows are served. Language text is in question_translation.';
comment on column public.question.hints is 'Ordered hint levels 1 to 3 (AI_Engine_Spec §6.3), e.g. [{"level": 1, "text": "..."}, ...].';
comment on column public.question.rubric is 'Object: {"criteria": [{"key": "...", "weight": 0.4, "description": "...", "levels": {"1": "...", ..., "5": "..."}}]}; criteria weights sum to 1.0 (validated by the seed loader).';
comment on column public.question.deterministic_check is '{"type": "truth_table" | "numeric" | "sim", "spec": {...}} (Data_Models §13.4).';
comment on column public.question.choices is 'Multiple choice: options, correct index, and the misconception each distractor represents.';

create index question_status_subject_difficulty_idx on public.question (status, subject_id, difficulty);
-- serves "status = 'published' and practice_modes @> '{quick}'" (spec index (status, practice_modes))
create index question_published_modes_gin           on public.question using gin (practice_modes) where status = 'published';
create index question_variation_of_idx              on public.question (variation_of_id) where variation_of_id is not null;
create index question_origin_idx                    on public.question (origin);

-- times_served is bumped on every serve; leave room for HOT updates
alter table public.question set (fillfactor = 90);

create trigger question_set_updated_at
  before update on public.question
  for each row execute function public.set_updated_at();

create trigger question_subject_is_domain
  before insert or update of subject_id on public.question
  for each row execute function public.enforce_skill_node_type('subject_id', 'domain');

-- §13.2  Question_Skill: which leaf skills a question gives evidence for
create table public.question_skill (
  question_id   uuid not null references public.question(id) on delete cascade,
  skill_id      uuid not null references public.skill(id) on delete restrict,
  weight        numeric(4,3) not null check (weight > 0 and weight <= 1),
  is_primary    boolean not null default false,
  primary key (question_id, skill_id)
);

comment on table public.question_skill is 'Share of a question''s evidence per skill; weights sum to 1.0 per question (validated by the seed loader).';

create index question_skill_skill_idx on public.question_skill (skill_id);
-- bank-first selection (AI_Engine_Spec §1.2): "published questions whose primary skill is X"
create index question_skill_primary_by_skill_idx on public.question_skill (skill_id, question_id) where is_primary;
-- at most one primary skill per question (the seed loader checks that exactly one exists)
create unique index question_skill_one_primary_idx on public.question_skill (question_id) where is_primary;

create trigger question_skill_skill_is_leaf
  before insert or update of skill_id on public.question_skill
  for each row execute function public.enforce_skill_node_type('skill_id', 'skill');

-- §13.3  Question_Translation
create table public.question_translation (
  question_id          uuid not null references public.question(id) on delete cascade,
  language             public.content_language not null,
  prompt               text not null,
  requirements         text,
  hints                jsonb,
  reference_solution   text,
  choices              jsonb,
  common_errors        jsonb,
  parity_checked       boolean not null default false,
  parity_checked_by    varchar(120),
  parity_checked_at    timestamptz,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now(),
  primary key (question_id, language),

  constraint question_translation_parity_chk check (
    parity_checked = false or (parity_checked_by is not null and parity_checked_at is not null)
  )
);

comment on table public.question_translation is 'Per-language text for a question. Served only when parity_checked (Data_Models §13.3, §17). Code, formulas and waveforms stay on question.assets.';

create trigger question_translation_set_updated_at
  before update on public.question_translation
  for each row execute function public.set_updated_at();

-- §17  Term_Glossary: technical terms; keep_english terms stay English inside Hebrew text
create table public.term_glossary (
  key            varchar(80) primary key,
  he             text not null,
  en             text not null,
  keep_english   boolean not null default false,
  notes          text,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

comment on table public.term_glossary is 'Technical term glossary for bilingual content (Data_Models §17). Injected into generated follow-ups, hints and tips.';

create trigger term_glossary_set_updated_at
  before update on public.term_glossary
  for each row execute function public.set_updated_at();
