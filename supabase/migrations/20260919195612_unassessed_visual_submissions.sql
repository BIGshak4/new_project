alter table public.attempt_submission drop constraint attempt_submission_answer_check;
alter table public.attempt_submission add constraint attempt_submission_answer_check check (
 length(answer) <= 20000 and (length(trim(answer)) > 0
 or coalesce(jsonb_array_length(visual_answer->'images'), 0) > 0
 or coalesce(jsonb_array_length(visual_answer #> '{circuit,parts}'), 0) > 0)
);
alter table public.attempt_submission drop constraint attempt_submission_done_chk;
alter table public.attempt_submission add constraint attempt_submission_done_chk check (
 status <> 'done' or (band is not null and evaluation is not null)
 or (visual_answer is not null and 'visual_review_pending' = any(flags)
     and band is null and evaluation is null and evidence_weight = 0)
);
