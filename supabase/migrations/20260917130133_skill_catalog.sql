-- ============================================================================
-- 0200  Skill catalog
-- Source: src/Data_Models.md §3 (Skill, Skill_Dependency)
-- ============================================================================

-- §3.1  Skill: two-level tree. `domain` rows group; only `skill` rows are examined.
create table public.skill (
  id                       uuid primary key default gen_random_uuid(),
  key                      varchar(80)  not null unique,
  label                    varchar(160) not null,
  description              text         not null,
  node_type                public.skill_node_type not null,
  parent_id                uuid references public.skill(id) on delete restrict,
  family                   public.skill_family   not null,
  category                 public.skill_category not null,
  default_assessment_mode  public.assessment_mode,           -- null for domains
  min_difficulty           smallint not null default 1  check (min_difficulty between 1 and 10),
  max_difficulty           smallint not null default 10 check (max_difficulty between 1 and 10),
  proficiency_rubric       jsonb    not null default '{}'::jsonb,
  is_active                boolean  not null default true,
  version                  integer  not null default 1,
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now(),

  constraint skill_difficulty_range_chk   check (min_difficulty <= max_difficulty),
  -- A leaf skill belongs to a domain; a domain has no parent (two-level tree).
  constraint skill_parent_by_type_chk     check (
    (node_type = 'domain' and parent_id is null) or
    (node_type = 'skill'  and parent_id is not null)
  ),
  -- Leaf skills must declare how they are examined; domains carry no mode.
  constraint skill_mode_by_type_chk       check (
    (node_type = 'domain' and default_assessment_mode is null) or
    (node_type = 'skill'  and default_assessment_mode is not null)
  ),
  constraint skill_rubric_is_object_chk   check (jsonb_typeof(proficiency_rubric) = 'object')
);

comment on table  public.skill is 'Shared skill catalog (Data_Models §3.1). Domains group leaf skills; only leaf skills are scored.';
comment on column public.skill.proficiency_rubric is 'Level 1-5 descriptors for this skill, e.g. {"1": "...", ..., "5": "..."} (Data_Models §3.4).';

create index skill_family_category_idx on public.skill (family, category);
create index skill_parent_id_idx       on public.skill (parent_id);

create trigger skill_set_updated_at
  before update on public.skill
  for each row execute function public.set_updated_at();

-- parent_id must point at a domain row
create trigger skill_parent_is_domain
  before insert or update of parent_id on public.skill
  for each row execute function public.enforce_skill_node_type('parent_id', 'domain');

-- node_type is immutable once set. The enforce_skill_node_type triggers on the
-- referencing tables only run when the referencing row is written, so flipping a
-- domain to a skill (or the reverse) would silently break every reference to it.
create or replace function public.forbid_skill_node_type_change()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.node_type is distinct from old.node_type then
    raise exception 'skill.node_type is immutable (% is a %)', old.key, old.node_type
      using errcode = 'check_violation';
  end if;
  return new;
end;
$$;

create trigger skill_node_type_immutable
  before update of node_type on public.skill
  for each row execute function public.forbid_skill_node_type_change();

-- §3.2  Skill_Dependency: prerequisite links the engine steps back along.
create table public.skill_dependency (
  skill_id               uuid not null references public.skill(id) on delete cascade,
  prerequisite_skill_id  uuid not null references public.skill(id) on delete cascade,
  strength               numeric(3,2) not null default 0.50 check (strength between 0 and 1),
  primary key (skill_id, prerequisite_skill_id),
  constraint skill_dependency_not_self_chk check (skill_id <> prerequisite_skill_id)
);

comment on table public.skill_dependency is 'Prerequisite links between leaf skills (Data_Models §3.2). Only add links a practitioner would agree with.';

create index skill_dependency_prerequisite_idx on public.skill_dependency (prerequisite_skill_id);

create trigger skill_dependency_skill_is_leaf
  before insert or update of skill_id on public.skill_dependency
  for each row execute function public.enforce_skill_node_type('skill_id', 'skill');

create trigger skill_dependency_prereq_is_leaf
  before insert or update of prerequisite_skill_id on public.skill_dependency
  for each row execute function public.enforce_skill_node_type('prerequisite_skill_id', 'skill');
