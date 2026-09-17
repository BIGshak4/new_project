-- ============================================================================
-- 1000  Row-level security
-- Source: HANDOFF.md §6 (policy intent), src/System_Architecture.md §6,
--         src/Data_Models.md §3.4 ("Raw 0-100 scores stay internal")
--
-- Model:
--   * The FastAPI backend uses the service role, which bypasses RLS and every
--     grant below, and is the only writer for content, sessions, attempts and
--     every evaluation table.
--   * Signed-in users (role `authenticated`) can read the catalog, roles, public
--     companies and their own rows. They can edit a limited set of profile
--     columns, mark their own notifications as opened, and add or delete their
--     own documents.
--   * `question`, `question_skill`, `question_translation` and `tips_library`
--     have NO user policies: RLS is per row, so "read published questions" would
--     expose reference_solution and all hints. The backend serves questions.
--   * Column-level grants withhold private or internal columns from clients:
--       session_turn          SELECT without expected_answer_outline, question_generation_meta
--       interview_session     SELECT without state (live engine state, raw scores)
--       user_skill_assessment SELECT without knowledge_score, confidence_score
--       user_skill_profile    SELECT without knowledge_score, confidence_score
--       evaluation_metrics    SELECT without the four raw before/after scores
--       daily_challenge       SELECT without participants, success_rate (shown after answering)
--       user_profile          UPDATE limited to preference columns
--       notification          UPDATE limited to opened_at
--       user_document         INSERT limited to user_id, doc_type, storage_key
--     With a column-level SELECT grant, clients must name columns instead of `*`.
--   * Anonymous users (`anon`) get nothing, now and for tables created later.
-- ============================================================================

-- ---- Enable RLS on every table -------------------------------------------------
alter table public.skill                  enable row level security;
alter table public.skill_dependency       enable row level security;
alter table public.user_profile           enable row level security;
alter table public.role_template          enable row level security;
alter table public.role_skill_set         enable row level security;
alter table public.company_profile        enable row level security;
alter table public.company_evidence       enable row level security;
alter table public.company_skill_set      enable row level security;
alter table public.question               enable row level security;
alter table public.question_skill         enable row level security;
alter table public.question_translation   enable row level security;
alter table public.term_glossary          enable row level security;
alter table public.tips_library           enable row level security;
alter table public.interview_session      enable row level security;
alter table public.session_skill_plan     enable row level security;
alter table public.session_turn           enable row level security;
alter table public.attempt                enable row level security;
alter table public.delivered_tip          enable row level security;
alter table public.user_document          enable row level security;
alter table public.evaluation_metrics     enable row level security;
alter table public.user_skill_assessment  enable row level security;
alter table public.skill_set_scorecard    enable row level security;
alter table public.user_skill_profile     enable row level security;
alter table public.session_report         enable row level security;
alter table public.learning_plan          enable row level security;
alter table public.plan_item              enable row level security;
alter table public.daily_challenge        enable row level security;
alter table public.user_engagement        enable row level security;
alter table public.notification           enable row level security;
alter table public.usage_event            enable row level security;

-- ---- Content readable by any signed-in user -------------------------------------
create policy "skill: authenticated read"
  on public.skill for select to authenticated
  using (true);

create policy "skill_dependency: authenticated read"
  on public.skill_dependency for select to authenticated
  using (true);

-- system roles for everyone; user-derived roles only for their owner. Inactive
-- roles stay readable because past sessions and plans are pinned to them; the
-- client filters is_active when listing roles to start something new.
create policy "role_template: authenticated read"
  on public.role_template for select to authenticated
  using (origin = 'system' or owner_user_id = (select auth.uid()));

-- visible when the parent role is visible (the subquery is itself filtered by role_template's policy)
create policy "role_skill_set: authenticated read"
  on public.role_skill_set for select to authenticated
  using (exists (select 1 from public.role_template r where r.id = role_template_id));

create policy "company_profile: authenticated read public"
  on public.company_profile for select to authenticated
  using (is_public);

create policy "company_evidence: authenticated read"
  on public.company_evidence for select to authenticated
  using (exists (select 1 from public.company_profile c where c.id = company_profile_id));

create policy "company_skill_set: authenticated read"
  on public.company_skill_set for select to authenticated
  using (exists (select 1 from public.company_profile c where c.id = company_profile_id));

create policy "term_glossary: authenticated read"
  on public.term_glossary for select to authenticated
  using (true);

-- today's and past challenges only; counters are returned by the backend after answering
create policy "daily_challenge: authenticated read"
  on public.daily_challenge for select to authenticated
  using (date <= current_date);

revoke select on public.daily_challenge from authenticated;
grant select (id, date, language, question_id, created_at) on public.daily_challenge to authenticated;

-- question, question_skill, question_translation, tips_library: no user policies (service role only).

-- ---- User profile: read own row, edit preference columns -----------------------------
create policy "user_profile: read own"
  on public.user_profile for select to authenticated
  using (id = (select auth.uid()));

create policy "user_profile: update own"
  on public.user_profile for update to authenticated
  using (id = (select auth.uid()))
  with check (id = (select auth.uid()));

-- plan_tier, consent records, targets (need referential checks), diagnostic
-- completion and timestamps are set by the backend
revoke update on public.user_profile from authenticated;
grant update (
  display_name, experience_years, seniority_self_assessed, background,
  interface_language, practice_language, target_interview_date,
  available_minutes_per_day, notification_prefs, target_families, locale
) on public.user_profile to authenticated;

-- ---- Sessions and practice: read own ---------------------------------------------
create policy "interview_session: read own"
  on public.interview_session for select to authenticated
  using (user_id = (select auth.uid()));

-- state holds live engine internals (raw scores, provisional levels, budgets)
revoke select on public.interview_session from authenticated;
grant select (
  id, user_id, role_template_id, role_template_version, company_profile_id,
  company_profile_version, seniority, baseline_difficulty, difficulty_ceiling,
  status, config, turn_count, hints_used, hints_requested_by_user, b2b_eligible,
  started_at, ended_at, created_at
) on public.interview_session to authenticated;

create policy "session_skill_plan: read own"
  on public.session_skill_plan for select to authenticated
  using (exists (
    select 1 from public.interview_session s
    where s.id = session_id and s.user_id = (select auth.uid())
  ));

create policy "session_turn: read own"
  on public.session_turn for select to authenticated
  using (exists (
    select 1 from public.interview_session s
    where s.id = session_id and s.user_id = (select auth.uid())
  ));

-- expected_answer_outline is private to the evaluator; question_generation_meta is internal
revoke select on public.session_turn from authenticated;
grant select (
  id, session_id, turn_index, skill_id, question_id, question_archetype, difficulty,
  question_text, answer_text, answer_code, answer_language, check_result,
  answer_started_at, answer_submitted_at, created_at
) on public.session_turn to authenticated;

create policy "attempt: read own"
  on public.attempt for select to authenticated
  using (user_id = (select auth.uid()));

create policy "delivered_tip: read own"
  on public.delivered_tip for select to authenticated
  using (
    exists (select 1 from public.interview_session s where s.id = session_id and s.user_id = (select auth.uid()))
    or
    exists (select 1 from public.attempt a where a.id = attempt_id and a.user_id = (select auth.uid()))
  );

create policy "user_document: read own"
  on public.user_document for select to authenticated
  using (user_id = (select auth.uid()));

create policy "user_document: insert own"
  on public.user_document for insert to authenticated
  with check (user_id = (select auth.uid()));

create policy "user_document: delete own"
  on public.user_document for delete to authenticated
  using (user_id = (select auth.uid()));

-- clients supply only the upload facts; parse_status, parsed_payload, id and
-- uploaded_at take their defaults and are written by the backend's parser
revoke insert on public.user_document from authenticated;
grant insert (user_id, doc_type, storage_key) on public.user_document to authenticated;

-- ---- Evaluation: read own, written only by the backend ----------------------------
create policy "evaluation_metrics: read own"
  on public.evaluation_metrics for select to authenticated
  using (user_id = (select auth.uid()) and anonymized_at is null);

-- raw 0-100 knowledge and confidence scores stay internal (Data_Models §3.4)
revoke select on public.evaluation_metrics from authenticated;
grant select (
  id, session_id, turn_id, attempt_id, mode, user_id,
  role_template_id, role_template_version, company_profile_id, family, sub_family, seniority, turn_index,
  subject_id, subject_status_before, subject_status_after, subject_turns_used, subject_turns_planned,
  entry_difficulty_reason, skill_id, skill_source, skill_combined_weight, skill_required_level,
  question_archetype, difficulty_asked, evidence_weight, check_passed, familiarity,
  correctness, depth, clarity, structure, tradeoff_reasoning, risk_awareness, hedging_ratio,
  observed_skill_scores, response_latency_ms, answer_duration_ms, answer_length_tokens, revision_count,
  provisional_level_after, decision_action, decision_reason_code, difficulty_next, skill_next_id,
  subject_next_id, subject_switch, hint_delivered, hint_level, hint_requested_by_user, tip_delivered_id,
  struggle_budget_remaining, recovered_after_hint, evaluator_model, evaluator_version,
  decision_engine_version, eval_latency_ms, eval_flags, b2b_eligible, created_at
) on public.evaluation_metrics to authenticated;

create policy "user_skill_assessment: read own"
  on public.user_skill_assessment for select to authenticated
  using (user_id = (select auth.uid()));

revoke select on public.user_skill_assessment from authenticated;
grant select (
  id, session_id, user_id, skill_id, source, assessment_mode, status, turns_count,
  demonstrated_ceiling, proficiency_level, required_level, level_gap, meets_requirement,
  hints_used, evidence_turn_ids, strengths, gaps, evaluator_version, created_at
) on public.user_skill_assessment to authenticated;

create policy "skill_set_scorecard: read own"
  on public.skill_set_scorecard for select to authenticated
  using (user_id = (select auth.uid()));

create policy "user_skill_profile: read own"
  on public.user_skill_profile for select to authenticated
  using (user_id = (select auth.uid()));

revoke select on public.user_skill_profile from authenticated;
grant select (
  id, user_id, skill_id, proficiency_level, level_score, assessments_count, evidence_turns_total,
  trend, level_history, first_assessed_at, last_assessed_at,
  retention_due_at, retention_checks_passed, last_retention_check_at, updated_at
) on public.user_skill_profile to authenticated;

create policy "session_report: read own"
  on public.session_report for select to authenticated
  using (exists (
    select 1 from public.interview_session s
    where s.id = session_id and s.user_id = (select auth.uid())
  ));

-- ---- Plan, engagement, usage: read own ---------------------------------------------
create policy "learning_plan: read own"
  on public.learning_plan for select to authenticated
  using (user_id = (select auth.uid()));

create policy "plan_item: read own"
  on public.plan_item for select to authenticated
  using (exists (
    select 1 from public.learning_plan p
    where p.id = plan_id and p.user_id = (select auth.uid())
  ));

create policy "user_engagement: read own"
  on public.user_engagement for select to authenticated
  using (user_id = (select auth.uid()));

create policy "notification: read own"
  on public.notification for select to authenticated
  using (user_id = (select auth.uid()));

create policy "notification: update own"
  on public.notification for update to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

-- users may only mark a notification as opened
revoke update on public.notification from authenticated;
grant update (opened_at) on public.notification to authenticated;

create policy "usage_event: read own"
  on public.usage_event for select to authenticated
  using (user_id = (select auth.uid()));

-- ---- Anonymous role: no access to any application table, now or later ---------------
revoke all on all tables in schema public from anon;
alter default privileges for role postgres in schema public revoke all on tables from anon;
