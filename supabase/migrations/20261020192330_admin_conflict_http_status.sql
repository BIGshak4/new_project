-- Optimistic edit conflicts are HTTP 409, not PostgreSQL serialization failures.
-- Avoid proxy/database retries for an intentional stale-edit rejection.
-- Existing signatures, privileges, founder checks and atomic writes are retained.

create or replace function jobrun_private.jr_admin_update_user(p_user_id uuid,p_plan_tier text,p_pilot_access boolean,p_expected_plan text,p_expected_access boolean) returns jsonb
language plpgsql security definer set search_path='' as $$
declare caller uuid := jobrun_private.jr_require_admin(); person auth.users%rowtype;
  old_plan text; old_access boolean; founder boolean; member_name text;
begin
  if p_user_id is null or p_plan_tier is null or p_plan_tier not in ('free','pro','team') or p_pilot_access is null or p_expected_plan is null or p_expected_access is null then
    raise exception 'invalid_input' using errcode='22023';
  end if;
  -- The Auth row exists even when a profile/membership is absent. It serializes
  -- concurrent plan/access updates without granting direct profile writes.
  select * into person from auth.users where id=p_user_id and deleted_at is null for update;
  if not found or person.email is null then raise exception 'user_unavailable' using errcode='22023'; end if;
  select coalesce(p.plan_tier::text,'free'),coalesce(p.display_name,'') into old_plan,member_name
    from public.user_profile p where p.id=p_user_id;
  old_plan:=coalesce(old_plan,'free');
  select exists(select 1 from public.jr_members where email=lower(person.email)),
    exists(select 1 from public.jr_members where email=lower(person.email) and can_manage_tasks)
    into old_access,founder;
  if old_plan<>p_expected_plan or old_access<>p_expected_access then raise exception 'conflict_reload' using errcode='PT409'; end if;
  if founder and not p_pilot_access then raise exception 'founder_access_protected' using errcode='42501'; end if;
  insert into public.user_profile(id,plan_tier) values(p_user_id,p_plan_tier::public.plan_tier)
    on conflict(id) do update set plan_tier=excluded.plan_tier;
  if p_pilot_access then
    insert into public.jr_members(email,display_name,can_manage_tasks)
      values(lower(person.email),coalesce(nullif(member_name,''),split_part(person.email,'@',1)),false)
      on conflict(email) do nothing;
  else
    delete from public.jr_members where email=lower(person.email) and not can_manage_tasks;
  end if;
  insert into public.jr_admin_events(actor_id,target_user_id,action,details)
    values(caller,p_user_id,'user_updated',jsonb_build_object('plan_before',old_plan,'plan_after',p_plan_tier,
      'pilot_access_before',old_access,'pilot_access_after',p_pilot_access,'billing','manual_no_charge'));
  return jobrun_private.jr_admin_user_row(p_user_id);
end $$;

create or replace function jobrun_private.jr_admin_update_support(p_id uuid,p_expected_version integer,p_status text,p_priority text,p_assigned_to uuid,p_internal_notes text,p_resolution text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_require_admin(); before_row public.jr_support_reports%rowtype;
begin
  if p_expected_version is null or p_status is null or p_status not in ('open','in_progress','waiting','resolved','closed')
    or p_priority is null or p_priority not in ('low','normal','high') or p_internal_notes is null or length(p_internal_notes)>10000
    or p_resolution is null or length(p_resolution)>5000 then raise exception 'invalid_input' using errcode='22023'; end if;
  if p_assigned_to is not null and not exists(select 1 from auth.users u join public.jr_members m on m.email=lower(u.email)
    where u.id=p_assigned_to and m.can_manage_tasks and u.email_confirmed_at is not null and u.deleted_at is null) then
    raise exception 'invalid_assignee' using errcode='22023';
  end if;
  select * into before_row from public.jr_support_reports where id=p_id for update;
  if not found then raise exception 'report_unavailable' using errcode='22023'; end if;
  if before_row.version<>p_expected_version then raise exception 'conflict_reload' using errcode='PT409'; end if;
  update public.jr_support_reports set status=p_status,priority=p_priority,assigned_to=p_assigned_to,
    internal_notes=p_internal_notes,resolution=p_resolution,version=version+1,updated_at=now() where id=p_id;
  insert into public.jr_admin_events(actor_id,report_id,action,details) values(caller,p_id,'report_updated',
    jsonb_build_object('status_before',before_row.status,'status_after',p_status,'priority_before',before_row.priority,'priority_after',p_priority,
      'assigned_before',before_row.assigned_to,'assigned_after',p_assigned_to,'internal_notes_changed',before_row.internal_notes<>p_internal_notes,
      'resolution_changed',before_row.resolution<>p_resolution,'version',before_row.version+1));
  return jobrun_private.jr_admin_support_row(p_id);
end $$;
