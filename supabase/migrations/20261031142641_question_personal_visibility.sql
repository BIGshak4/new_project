-- Personal library state; hidden never changes the learner's completion or notes.
alter table public.jr_practice_entries
  add column hidden boolean not null default false;

-- Alias records keep their identities and histories. Patch their personal flags
-- together so a legacy search result cannot resurrect a hidden question.
-- SECURITY INVOKER retains the table's existing owner/member RLS checks.
create function public.jr_set_question_state(
  p_question_ids uuid[],
  p_completed boolean default null,
  p_hidden boolean default null
)
returns setof public.jr_practice_entries
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if auth.uid() is null then
    raise exception 'Authentication required' using errcode = '42501';
  end if;
  if coalesce(cardinality(p_question_ids), 0) not between 1 and 8
     or array_position(p_question_ids, null) is not null
     or (p_completed is null and p_hidden is null) then
    raise exception 'Invalid personal question state' using errcode = '22023';
  end if;

  return query
  insert into public.jr_practice_entries as entry (user_id, question_id, completed, hidden)
  select auth.uid(), q.id, coalesce(p_completed, false), coalesce(p_hidden, false)
  from (select distinct unnest(p_question_ids) as id) q
  order by q.id
  on conflict (user_id, question_id) do update
    set completed = coalesce(p_completed, entry.completed),
        hidden = coalesce(p_hidden, entry.hidden)
  returning entry.*;
end;
$$;

revoke all on function public.jr_set_question_state(uuid[], boolean, boolean) from public, anon, service_role;
grant execute on function public.jr_set_question_state(uuid[], boolean, boolean) to authenticated;
