-- ============================================================================
-- 0100  Enums and shared functions
-- Source: src/Data_Models.md v2.1 (all sections), src/AI_Engine_Spec.md v2.1
-- Every enum type used by later migrations is defined here so the vocabulary
-- is in one place. Two helper trigger functions are defined at the bottom.
-- ============================================================================

-- ---- People and roles -------------------------------------------------------
create type public.seniority as enum
  ('student', 'junior', 'mid', 'senior', 'staff', 'principal');

create type public.role_family as enum
  ('hardware', 'software', 'cross_family');

create type public.role_origin as enum
  ('system', 'user_derived');

create type public.plan_tier as enum
  ('free', 'pro', 'team');

-- ---- Skill catalog ------------------------------------------------------------
create type public.skill_node_type as enum
  ('domain', 'skill');

create type public.skill_family as enum
  ('hardware', 'software', 'general');

create type public.skill_category as enum
  ('technical', 'problem_solving', 'communication', 'collaboration', 'culture');

create type public.assessment_mode as enum
  ('questioned', 'observed');

create type public.importance as enum
  ('core', 'important', 'nice_to_have');

-- Where a skill in a session plan came from (Data_Models §6.2)
create type public.skill_source as enum
  ('role', 'company', 'role_and_company', 'user_focus');

-- ---- Companies ----------------------------------------------------------------
create type public.company_scope as enum
  ('all_roles', 'family', 'role');

create type public.evidence_source_type as enum
  ('official_guidance', 'candidate_report', 'mock_or_prep_example', 'our_recommendation');

create type public.evidence_confidence as enum
  ('high', 'medium', 'low');

-- ---- Localization ---------------------------------------------------------------
create type public.content_language as enum
  ('he', 'en');

-- ---- Question bank (Data_Models §13) -----------------------------------------
create type public.question_status as enum
  ('draft', 'in_review', 'published', 'withheld', 'retired');

create type public.question_origin as enum
  ('original', 'licensed', 'ai_assisted_reviewed', 'ai_generated');

create type public.question_format as enum
  ('multiple_choice', 'short_answer', 'construct', 'code', 'hdl', 'waveform', 'truth_table', 'explain');

create type public.question_archetype as enum
  ('conceptual', 'coding', 'debugging', 'design', 'behavioral');

create type public.reuse_status as enum
  ('permitted', 'attribution_required', 'pending_review', 'not_permitted');

create type public.exposure_risk as enum
  ('low', 'medium', 'high');

-- ---- Practice and sessions (Data_Models §6, §14) -----------------------------
create type public.practice_mode as enum
  ('quick', 'deep', 'simulation');

create type public.session_status as enum
  ('configured', 'in_progress', 'paused', 'completed', 'abandoned');

create type public.answer_band as enum
  ('STRONG', 'PARTIAL', 'WEAK');

create type public.familiarity as enum
  ('new', 'seen_variation', 'seen_same');

-- ---- Evaluation (Data_Models §7, §9) -----------------------------------------
create type public.assessment_status as enum
  ('assessed', 'insufficient_evidence', 'not_assessed');

create type public.scorecard_scope as enum
  ('role', 'company', 'session_overall');

create type public.skill_trend as enum
  ('improving', 'stable', 'declining', 'new');

-- ENTER_SKILL is the Subject Router's action when it opens a new skill or subject
-- (AI_Engine_Spec §5.2, Data_Models §11.1). PIVOT_TOPIC is kept for §9.2 conformance.
create type public.decision_action as enum
  ('ESCALATE', 'HOLD', 'HINT', 'STEP_BACK', 'PIVOT_TOPIC', 'ENTER_SKILL', 'END');

-- Subject Router status per subject (AI_Engine_Spec §4, Data_Models §9.2)
create type public.subject_status as enum
  ('untouched', 'exploring', 'strong', 'mixed', 'weak', 'done');

-- ---- Tips (Data_Models §8.2, §8.3) -------------------------------------------
create type public.tip_category as enum
  ('communication', 'problem_solving', 'technical', 'structure', 'time_management', 'confidence');

create type public.tip_delivery_timing as enum
  ('mid_session', 'post_session', 'both');

create type public.tip_origin as enum
  ('curated', 'ai_generated_pending_review', 'ai_generated_approved');

-- ---- Documents, plan, notifications (Data_Models §8.5, §15) ------------------
create type public.document_type as enum
  ('resume', 'job_description', 'reference');

create type public.parse_status as enum
  ('pending', 'parsed', 'failed');

-- Activity modes: the three practice modes plus the two plan-only activities that
-- carry their own evidence weights (AI_Engine_Spec §2.9). Used by plan_item.mode,
-- evaluation_metrics.mode and usage_event.mode.
create type public.activity_mode as enum
  ('quick', 'deep', 'simulation', 'diagnostic', 'retention_check');

create type public.plan_item_status as enum
  ('planned', 'started', 'done', 'skipped');

create type public.notification_channel as enum
  ('email', 'push');

-- ============================================================================
-- Shared trigger functions
-- ============================================================================

-- Keeps updated_at current on every UPDATE.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- Enforces that a column referencing public.skill points at the expected node
-- type. Usage:
--   create trigger ... execute function public.enforce_skill_node_type('skill_id', 'skill');
--   create trigger ... execute function public.enforce_skill_node_type('subject_id', 'domain');
-- Data_Models §3.1: only leaf `skill` rows are examined; `domain` rows group them.
create or replace function public.enforce_skill_node_type()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  col        text := tg_argv[0];
  expected   public.skill_node_type := tg_argv[1]::public.skill_node_type;
  target_id  uuid;
  actual     public.skill_node_type;
begin
  target_id := (to_jsonb(new) ->> col)::uuid;
  if target_id is null then
    return new;
  end if;

  select s.node_type into actual
  from public.skill s
  where s.id = target_id;

  if actual is distinct from expected then
    raise exception '%.% must reference a skill row with node_type = % (got %)',
      tg_table_name, col, expected, coalesce(actual::text, 'no such skill')
      using errcode = 'check_violation';
  end if;

  return new;
end;
$$;
