-- ============================================================================
-- 1300  Client read grants for tables whose policies were unreachable
--
-- 1000_rls wrote "read own" / "read catalog" policies for these tables and only
-- narrowed a few others column by column, assuming the default SELECT grant to
-- `authenticated` that Supabase gives new tables. On this project that default
-- did not apply to the migrated tables, so 20 tables carried a policy and no
-- grant: a signed-in browser got "permission denied" instead of its own rows.
-- Found by the live access-boundary test (tests/test_live_service.py).
--
-- Row scope is still the policies' job; this only makes them reachable. Columns
-- that are internal to the engine stay withheld (attempt.engine_state and the
-- raw attempt.evaluation), the same way attempt_submission and
-- user_skill_profile withhold theirs. `anon` keeps nothing.
-- ============================================================================

-- catalog (read by every signed-in user)
grant select on public.skill, public.skill_dependency, public.role_template, public.role_skill_set,
                public.company_profile, public.company_evidence, public.company_skill_set, public.term_glossary
  to authenticated;

-- own rows
grant select on public.user_profile, public.session_skill_plan, public.session_report, public.delivered_tip,
                public.skill_set_scorecard, public.learning_plan, public.plan_item, public.user_engagement,
                public.notification, public.usage_event
  to authenticated;

grant select (
  id, user_id, question_id, question_version, mode, plan_item_id, practice_language, self_confidence_before,
  answer, check_result, band, hints_used, reference_revealed, revealed_before_submit, follow_up_turns,
  misconceptions_hit, familiarity, duration_ms, started_at, submitted_at, evaluator_version, exposures
) on public.attempt to authenticated;

-- user_document: "read own" and "delete own" policies exist; insert is already column-limited
grant select, delete on public.user_document to authenticated;

revoke all on all tables in schema public from anon;
