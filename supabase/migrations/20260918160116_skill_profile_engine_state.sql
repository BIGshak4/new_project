-- ============================================================================
-- 1200  Engine state on the skill profile (backend step 4b, stage C)
--
-- user_skill_profile keeps the typed, client-readable summary of a skill
-- (proficiency_level, trend, counts, retention). The engine's full per-skill
-- state (struggle budget, ceiling, hint level, turn history, controller status)
-- has no home in those columns, so it lives here as one JSON object, the same
-- way attempt.engine_state does. The typed columns are derived from it on every
-- write. The column is internal: the column-level SELECT grant in 1000_rls does
-- not include it, so clients never see raw engine state.
-- ============================================================================

alter table public.user_skill_profile
  add column engine_state jsonb not null default '{}'::jsonb,
  add constraint user_skill_profile_engine_state_object_chk check (jsonb_typeof(engine_state) = 'object');

comment on column public.user_skill_profile.engine_state is
  'Full engine SkillState (app/schemas/engine.py) as JSON. Source of truth for the engine; the typed columns are derived from it. Not readable by clients.';
