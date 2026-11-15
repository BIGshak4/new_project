-- Older main answers were saved before submission also marked the library question done.
-- submitted_at is set only after a main answer is accepted (never on a visit or a draft).
insert into public.jr_practice_entries as entry (user_id, question_id, completed, updated_at)
select user_id, question_id, true, max(submitted_at)
from public.attempt
where submitted_at is not null
group by user_id, question_id
order by user_id, question_id
on conflict (user_id, question_id) do update
set completed = true
-- A later user edit may have explicitly unchecked this question; preserve that choice.
where not entry.completed and entry.updated_at < excluded.updated_at;
