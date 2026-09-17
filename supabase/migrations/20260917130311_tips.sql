-- ============================================================================
-- 0600  Tips library
-- Source: src/Data_Models.md §8.2 (Tips_Library)
-- Delivered_Tip is in 0700 because it references session_turn and attempt.
-- ============================================================================

create table public.tips_library (
  id                     uuid primary key default gen_random_uuid(),
  key                    varchar(80) not null unique,
  category               public.tip_category not null,
  trigger_conditions     jsonb not null,
  applicable_families    text[] not null default '{}',
  applicable_skill_ids   uuid[] not null default '{}',
  improves_skill_ids     uuid[] not null default '{}',
  tip_template           text not null,
  example_before         text,
  example_after          text,
  delivery_timing        public.tip_delivery_timing not null default 'both',
  severity               smallint not null default 3 check (severity between 1 and 5),
  origin                 public.tip_origin not null default 'curated',
  effectiveness_score    numeric(5,4) check (effectiveness_score between 0 and 1),
  times_delivered        integer not null default 0 check (times_delivered >= 0),
  is_active              boolean not null default true,
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now(),

  constraint tips_library_trigger_is_object_chk check (jsonb_typeof(trigger_conditions) = 'object'),
  -- matched against the role family of the session or plan (hardware, software, cross_family); general = any
  constraint tips_library_families_chk check (applicable_families <@ array['hardware', 'software', 'cross_family', 'general']::text[])
);

comment on table  public.tips_library is 'Coaching tips matched by rules (Data_Models §8.2). Empty applicable_* arrays mean "all".';
comment on column public.tips_library.trigger_conditions is '{"any_of": [...], "all_of": [...], "cooldown_turns": N}; machine-matched in engine/tips.py.';
comment on column public.tips_library.tip_template is 'Text with {{placeholders}}; polished into the practice language by the LLM.';

create index tips_library_category_active_idx on public.tips_library (category, is_active);

create trigger tips_library_set_updated_at
  before update on public.tips_library
  for each row execute function public.set_updated_at();
