-- The question bank is already backend-only. Do not expose its ratings through
-- the signed-in user's own interview turns, evaluation metrics, or saved reports.
revoke select (difficulty) on public.session_turn from public, anon, authenticated;
revoke select (entry_difficulty_reason, difficulty_asked, difficulty_next)
  on public.evaluation_metrics from public, anon, authenticated;
-- The demonstrated ceiling can identify the exact rating of a single cited turn.
revoke select (demonstrated_ceiling) on public.user_skill_assessment from public, anon, authenticated;

-- session_report had a table-wide SELECT grant; removing one column alone
-- would not override it. Generated prose is served through the current API:
-- historical narratives and arbitrary generator metadata may include a rating.
revoke select on public.session_report from public, anon, authenticated;
revoke select (difficulty_timeline, generation_meta, narrative_md)
  on public.session_report from public, anon, authenticated;
grant select (
  id, session_id, role_scorecard_id, company_scorecard_id, overall_scorecard_id,
  top_tips, recommended_next_skills, generated_at
) on public.session_report to authenticated;
