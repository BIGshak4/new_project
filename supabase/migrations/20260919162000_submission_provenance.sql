-- ============================================================================
-- 1400  Who judged each answer (backend P0: demo vs real assessment)
--
-- While LLM_PROVIDER=scripted the backend writes demonstration evaluations. Once a
-- real model is switched on, those rows must never be shown or counted as real.
-- Each revision now records the model that judged it; the API derives
-- assessed_by = 'demo' | 'model' from it. Readable by the owner (a learner may
-- know whether their feedback was real).
-- ============================================================================

alter table public.attempt_submission
  add column evaluator_model varchar(80);

comment on column public.attempt_submission.evaluator_model is
  'Model id that produced this revision''s evaluation; ''demo'' / ''scripted'' / ''manual'' are stand-ins, never real evidence.';

grant select (evaluator_model) on public.attempt_submission to authenticated;
