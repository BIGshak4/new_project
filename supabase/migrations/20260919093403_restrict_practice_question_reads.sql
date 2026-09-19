-- Deploy the practice-API frontend before applying this migration.
-- Question bodies, hidden hints, rubrics, check answers and references are served
-- through the authenticated backend, which records exposure on each attempt.
-- Supabase REST remains available for the learner's own jr_practice_entries.
revoke all privileges on public.question, public.question_translation
  from public, anon, authenticated;

-- Table-level REVOKE does not remove independently granted column privileges.
do $$
declare
  target regclass;
  columns_sql text;
begin
  foreach target in array array['public.question'::regclass, 'public.question_translation'::regclass]
  loop
    select string_agg(quote_ident(attname), ', ' order by attnum)
      into columns_sql
      from pg_attribute where attrelid = target and attnum > 0 and not attisdropped;
    execute format('revoke select (%1$s), insert (%1$s), update (%1$s), references (%1$s) on %2$s from public, anon, authenticated', columns_sql, target);
  end loop;
end $$;

drop policy if exists "founders review example questions" on public.question;
drop policy if exists "founders review example translations" on public.question_translation;
-- RLS stays enabled with no browser policies by design. Backend owner access is unchanged.

-- This JSON includes expected_answer_outline for generated follow-ups. The API
-- returns only each follow-up's question and saved submission to the learner.
revoke select (follow_up_turns) on public.attempt from public, anon, authenticated;
