-- code_tests: a deterministic check that runs the Python in a candidate's answer against the
-- question's test cases in an isolated child interpreter (backend/app/engine/code_runner.py).
-- question_check_type_chk lists the check types a question may carry; it gains 'code_tests'.
-- Without this, seed_db.py cannot load the seven software questions that now carry one
-- (the insert fails the constraint, which is what the live suite showed on 2026-09-21).

alter table public.question drop constraint question_check_type_chk;

alter table public.question add constraint question_check_type_chk check (
  deterministic_check is null or (
    jsonb_typeof(deterministic_check) = 'object' and
    deterministic_check ->> 'type' in ('truth_table', 'numeric', 'sim', 'code_tests') and
    deterministic_check ? 'spec'
  )
);

comment on column public.question.deterministic_check is
  '{"type": "truth_table" | "numeric" | "sim" | "code_tests", "spec": {...}} (Data_Models §13.4). '
  'code_tests spec: {"language": "python", "entry": [function names], "timeout_ms": 5000, '
  '"cases": [{"args": [...], "expected": value} | {"args": [...], "accept": [values], "unordered": true}]}';
