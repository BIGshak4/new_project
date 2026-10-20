-- Founder administration and private support inbox. Additive: no existing
-- question, answer, assessment, task, or user record is replaced.
-- Paid plan labels are manual entitlements only; this migration takes no money.
-- Public RPCs are parsed SQL INVOKER wrappers. Their private DEFINER targets
-- perform live auth.users + founder checks and keep private-schema USAGE denied.

create table public.jr_support_reports (
  id uuid primary key,
  reporter_id uuid not null references auth.users(id) on delete cascade,
  subject text not null check (length(trim(subject)) between 1 and 160),
  description text not null check (length(trim(description)) between 1 and 10000),
  category text not null check (category in ('bug','question','feedback','other')),
  language text not null check (language in ('he','en')),
  page_path text not null default '/' check (length(page_path)<=1000 and left(page_path,1)='/' and left(page_path,2)<>'//' and page_path !~ '[[:cntrl:]]' and strpos(page_path,chr(92))=0),
  question_key text check (length(question_key)<=200),
  status text not null default 'open' check (status in ('open','in_progress','waiting','resolved','closed')),
  priority text not null default 'normal' check (priority in ('low','normal','high')),
  assigned_to uuid references auth.users(id) on delete set null,
  internal_notes text not null default '' check (length(internal_notes)<=10000),
  resolution text not null default '' check (length(resolution)<=5000),
  version integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index jr_support_reports_inbox_idx on public.jr_support_reports(status,created_at desc);
create index jr_support_reports_reporter_idx on public.jr_support_reports(reporter_id,created_at desc);
create index jr_support_reports_assigned_idx on public.jr_support_reports(assigned_to) where assigned_to is not null;
alter table public.jr_support_reports enable row level security;
revoke all on public.jr_support_reports from public,anon,authenticated;
-- Internal notes never have browser column privileges, even for the reporter.
grant select(id,reporter_id,subject,description,category,language,page_path,question_key,
  status,priority,assigned_to,resolution,version,created_at,updated_at)
  on public.jr_support_reports to authenticated;
create policy "support reporter reads own report" on public.jr_support_reports for select to authenticated
  using (reporter_id=(select auth.uid()));

create table public.jr_support_files (
  id uuid primary key,
  report_id uuid not null references public.jr_support_reports(id) on delete cascade,
  owner_id uuid not null references auth.users(id) on delete cascade,
  storage_path text not null unique,
  name text not null check(length(trim(name)) between 1 and 180 and name !~ '[[:cntrl:]]' and strpos(name,'/')=0 and strpos(name,chr(92))=0),
  mime_type text not null check(mime_type in ('image/png','image/jpeg','image/webp','application/pdf','text/plain')),
  size_bytes bigint not null check(size_bytes between 1 and 5242880),
  created_at timestamptz not null default now()
);
create index jr_support_files_report_idx on public.jr_support_files(report_id,created_at);
create index jr_support_files_owner_idx on public.jr_support_files(owner_id);
alter table public.jr_support_files enable row level security;
revoke all on public.jr_support_files from public,anon,authenticated;
grant select on public.jr_support_files to authenticated;
create policy "support reporter reads own file reservations" on public.jr_support_files for select to authenticated
  using(owner_id=(select auth.uid()));

create table public.jr_admin_events (
  id bigint generated always as identity primary key,
  actor_id uuid references auth.users(id) on delete set null,
  target_user_id uuid references auth.users(id) on delete set null,
  report_id uuid references public.jr_support_reports(id) on delete cascade,
  action text not null,
  details jsonb not null default '{}',
  created_at timestamptz not null default now()
);
create index jr_admin_events_report_idx on public.jr_admin_events(report_id,created_at);
create index jr_admin_events_user_idx on public.jr_admin_events(target_user_id,created_at);
create index jr_admin_events_actor_idx on public.jr_admin_events(actor_id);
alter table public.jr_admin_events enable row level security;
revoke all on public.jr_admin_events from public,anon,authenticated;

create function jobrun_private.jr_verified_user() returns uuid
language plpgsql stable security definer set search_path='' as $$
declare caller uuid := auth.uid();
begin
  if caller is null or not exists(select 1 from auth.users u where u.id=caller and u.email_confirmed_at is not null and u.deleted_at is null) then
    raise exception 'authentication_required' using errcode='42501';
  end if;
  return caller;
end $$;

create function jobrun_private.jr_require_admin() returns uuid
language plpgsql stable security definer set search_path='' as $$
declare caller uuid := jobrun_private.jr_verified_user();
begin
  if not exists(select 1 from auth.users u join public.jr_members m on m.email=lower(u.email)
      where u.id=caller and m.can_manage_tasks) then
    raise exception 'admin_access_required' using errcode='42501';
  end if;
  return caller;
end $$;

create function jobrun_private.jr_admin_user_row(p_user_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
  select jsonb_build_object('id',u.id,'email',u.email,'display_name',coalesce(p.display_name,''),
    'created_at',u.created_at,'last_sign_in_at',u.last_sign_in_at,
    'email_confirmed',u.email_confirmed_at is not null,'plan_tier',coalesce(p.plan_tier::text,'free'),
    'pilot_access',m.email is not null,'is_founder',coalesce(m.can_manage_tasks,false))
  from auth.users u left join public.user_profile p on p.id=u.id
  left join public.jr_members m on m.email=lower(u.email) where u.id=p_user_id;
$$;

create function jobrun_private.jr_admin_users(p_query text default '',p_page integer default 1,p_page_size integer default 25) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare result jsonb; total_count bigint;
begin
  perform jobrun_private.jr_require_admin();
  if p_query is null or length(p_query)>200 or p_page is null or p_page<1 or p_page>100000 or p_page_size is null or p_page_size not between 1 and 100 then
    raise exception 'invalid_input' using errcode='22023';
  end if;
  select count(*) into total_count from auth.users u left join public.user_profile p on p.id=u.id
    where u.deleted_at is null and (trim(p_query)='' or strpos(lower(concat_ws(' ',u.email,p.display_name,u.id::text)),lower(trim(p_query)))>0);
  select coalesce(jsonb_agg(jobrun_private.jr_admin_user_row(s.id) order by s.created_at desc,s.id),'[]'::jsonb) into result
    from (select u.id,u.created_at from auth.users u left join public.user_profile p on p.id=u.id
      where u.deleted_at is null and (trim(p_query)='' or strpos(lower(concat_ws(' ',u.email,p.display_name,u.id::text)),lower(trim(p_query)))>0)
      order by u.created_at desc,u.id limit p_page_size offset ((p_page-1)::bigint*p_page_size)) s;
  return jsonb_build_object('users',result,'total',total_count);
end $$;

create function jobrun_private.jr_admin_update_user(p_user_id uuid,p_plan_tier text,p_pilot_access boolean,p_expected_plan text,p_expected_access boolean) returns jsonb
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
  if old_plan<>p_expected_plan or old_access<>p_expected_access then raise exception 'conflict_reload' using errcode='40001'; end if;
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

create function jobrun_private.jr_support_public_row(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
  select to_jsonb(r)-'internal_notes' from public.jr_support_reports r where r.id=p_id;
$$;

create function jobrun_private.jr_submit_support_report(p_id uuid,p_subject text,p_description text,p_category text,p_language text,p_page_path text,p_question_key text default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_verified_user(); existing public.jr_support_reports%rowtype;
begin
  -- All creation/reservation operations for one user share this lock, bounding
  -- rate and storage quotas even across tabs, retries and independent workers.
  perform 1 from auth.users where id=caller for update;
  select * into existing from public.jr_support_reports where id=p_id;
  if found then
    if existing.reporter_id<>caller then raise exception 'report_unavailable' using errcode='42501'; end if;
    return jobrun_private.jr_support_public_row(p_id);
  end if;
  if p_id is null or p_subject is null or length(trim(p_subject)) not between 1 and 160
    or p_description is null or length(trim(p_description)) not between 1 and 10000
    or p_category is null or p_category not in ('bug','question','feedback','other')
    or p_language is null or p_language not in ('he','en') or p_page_path is null
    or length(p_page_path)>1000 or left(p_page_path,1)<>'/' or left(p_page_path,2)='//'
    or p_page_path ~ '[[:cntrl:]]' or strpos(p_page_path,chr(92))>0 or length(p_question_key)>200 then
    raise exception 'invalid_input' using errcode='22023';
  end if;
  if (select count(*) from public.jr_support_reports where reporter_id=caller and created_at>now()-interval '24 hours')>=5 then
    raise exception 'support_rate_limit' using errcode='23514';
  end if;
  insert into public.jr_support_reports(id,reporter_id,subject,description,category,language,page_path,question_key)
    values(p_id,caller,trim(p_subject),trim(p_description),p_category,p_language,p_page_path,nullif(trim(p_question_key),''));
  insert into public.jr_admin_events(actor_id,report_id,action) values(caller,p_id,'report_created');
  return jobrun_private.jr_support_public_row(p_id);
end $$;

create function jobrun_private.jr_reserve_support_file(p_id uuid,p_report_id uuid,p_name text,p_mime_type text,p_size_bytes bigint) returns jsonb
language plpgsql security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_verified_user(); report public.jr_support_reports%rowtype;
  existing public.jr_support_files%rowtype; suffix text; row_count bigint; byte_count bigint;
begin
  perform 1 from auth.users where id=caller for update;
  select * into report from public.jr_support_reports where id=p_report_id for update;
  if not found or report.reporter_id<>caller then raise exception 'report_unavailable' using errcode='42501'; end if;
  select * into existing from public.jr_support_files where id=p_id;
  if found then
    if existing.owner_id<>caller or existing.report_id<>p_report_id or existing.name is distinct from p_name
      or existing.mime_type is distinct from p_mime_type or existing.size_bytes is distinct from p_size_bytes then
      raise exception 'invalid_input' using errcode='22023';
    end if;
    return to_jsonb(existing)||jsonb_build_object('uploaded',exists(select 1 from storage.objects where bucket_id='jr-support-files' and name=existing.storage_path));
  end if;
  if report.status in ('resolved','closed') then raise exception 'report_unavailable' using errcode='42501'; end if;
  suffix:=case p_mime_type when 'image/png' then 'png' when 'image/jpeg' then 'jpg'
    when 'image/webp' then 'webp' when 'application/pdf' then 'pdf' when 'text/plain' then 'txt' end;
  if p_id is null or p_name is null or length(trim(p_name)) not between 1 and 180
    or p_name ~ '[[:cntrl:]]' or strpos(p_name,'/')>0 or strpos(p_name,chr(92))>0
    or suffix is null or p_size_bytes is null or p_size_bytes not between 1 and 5242880
    or (p_mime_type='image/jpeg' and lower(p_name) !~ '[.](jpg|jpeg)$')
    or (p_mime_type<>'image/jpeg' and right(lower(p_name),length(suffix)+1)<>'.'||suffix) then
    raise exception 'invalid_input' using errcode='22023';
  end if;
  select count(*),coalesce(sum(size_bytes),0) into row_count,byte_count from public.jr_support_files where report_id=p_report_id;
  if row_count>=5 or byte_count+p_size_bytes>15728640
    or (select coalesce(sum(size_bytes),0)+p_size_bytes from public.jr_support_files where owner_id=caller)>104857600 then
    raise exception 'support_file_quota' using errcode='23514';
  end if;
  insert into public.jr_support_files(id,report_id,owner_id,storage_path,name,mime_type,size_bytes)
    values(p_id,p_report_id,caller,caller::text||'/'||p_report_id::text||'/'||p_id::text||'.'||suffix,p_name,p_mime_type,p_size_bytes)
    returning * into existing;
  return to_jsonb(existing)||jsonb_build_object('uploaded',false);
end $$;

create function jobrun_private.jr_remove_support_file(p_id uuid) returns boolean
language plpgsql security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_verified_user(); entry public.jr_support_files%rowtype;
begin
  perform 1 from auth.users where id=caller for update;
  select f.* into entry from public.jr_support_files f join public.jr_support_reports r on r.id=f.report_id
    where f.id=p_id and f.owner_id=caller and r.reporter_id=caller for update of r,f;
  if not found then return true; end if;
  -- Upload persistence takes the same report lock: removal cannot orphan a
  -- concurrently completed upload. Existing uploads cannot be erased by clients.
  if exists(select 1 from storage.objects where bucket_id='jr-support-files' and name=entry.storage_path) then return false; end if;
  delete from public.jr_support_files where id=p_id;
  return true;
end $$;

create function jobrun_private.jr_support_assignees() returns jsonb
language sql stable security definer set search_path='' as $$
  select coalesce(jsonb_agg(jsonb_build_object('id',u.id,'email',u.email,'display_name',coalesce(p.display_name,m.display_name)) order by m.display_name),'[]'::jsonb)
    from auth.users u join public.jr_members m on m.email=lower(u.email)
    left join public.user_profile p on p.id=u.id
    where m.can_manage_tasks and u.email_confirmed_at is not null and u.deleted_at is null;
$$;

create function jobrun_private.jr_admin_support_row(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
  select to_jsonb(r)||jsonb_build_object('reporter_email',u.email,'reporter_name',coalesce(p.display_name,''),
    'file_count',(select count(*) from public.jr_support_files f join storage.objects o on o.bucket_id='jr-support-files' and o.name=f.storage_path where f.report_id=r.id))
  from public.jr_support_reports r join auth.users u on u.id=r.reporter_id
    left join public.user_profile p on p.id=u.id where r.id=p_id;
$$;

create function jobrun_private.jr_admin_support_list(p_query text default '',p_status text default 'all',p_page integer default 1,p_page_size integer default 25) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare rows jsonb; total_count bigint;
begin
  perform jobrun_private.jr_require_admin();
  if p_query is null or length(p_query)>200 or p_status is null or p_status not in ('all','open','in_progress','waiting','resolved','closed')
    or p_page is null or p_page<1 or p_page>100000 or p_page_size is null or p_page_size not between 1 and 100 then
    raise exception 'invalid_input' using errcode='22023';
  end if;
  select count(*) into total_count from public.jr_support_reports r join auth.users u on u.id=r.reporter_id
    where (p_status='all' or r.status=p_status) and (trim(p_query)='' or strpos(lower(concat_ws(' ',r.subject,r.description,u.email,r.id::text,r.question_key)),lower(trim(p_query)))>0);
  select coalesce(jsonb_agg(jobrun_private.jr_admin_support_row(s.id) order by s.created_at desc,s.id),'[]'::jsonb) into rows
    from (select r.id,r.created_at from public.jr_support_reports r join auth.users u on u.id=r.reporter_id
      where (p_status='all' or r.status=p_status) and (trim(p_query)='' or strpos(lower(concat_ws(' ',r.subject,r.description,u.email,r.id::text,r.question_key)),lower(trim(p_query)))>0)
      order by r.created_at desc,r.id limit p_page_size offset ((p_page-1)::bigint*p_page_size)) s;
  return jsonb_build_object('reports',rows,'total',total_count,'assignees',jobrun_private.jr_support_assignees());
end $$;

create function jobrun_private.jr_admin_support_detail(p_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare report jsonb; files jsonb; events jsonb;
begin
  perform jobrun_private.jr_require_admin();
  report:=jobrun_private.jr_admin_support_row(p_id);
  if report is null then raise exception 'report_unavailable' using errcode='22023'; end if;
  select coalesce(jsonb_agg(to_jsonb(f)||jsonb_build_object('uploaded',o.id is not null) order by f.created_at,f.id),'[]'::jsonb)
    into files from public.jr_support_files f left join storage.objects o on o.bucket_id='jr-support-files' and o.name=f.storage_path where f.report_id=p_id;
  select coalesce(jsonb_agg(to_jsonb(e)||jsonb_build_object('actor_email',u.email) order by e.created_at desc,e.id desc),'[]'::jsonb)
    into events from public.jr_admin_events e left join auth.users u on u.id=e.actor_id where e.report_id=p_id;
  return jsonb_build_object('report',report,'files',files,'events',events,'assignees',jobrun_private.jr_support_assignees());
end $$;

create function jobrun_private.jr_admin_update_support(p_id uuid,p_expected_version integer,p_status text,p_priority text,p_assigned_to uuid,p_internal_notes text,p_resolution text) returns jsonb
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
  if before_row.version<>p_expected_version then raise exception 'conflict_reload' using errcode='40001'; end if;
  update public.jr_support_reports set status=p_status,priority=p_priority,assigned_to=p_assigned_to,
    internal_notes=p_internal_notes,resolution=p_resolution,version=version+1,updated_at=now() where id=p_id;
  insert into public.jr_admin_events(actor_id,report_id,action,details) values(caller,p_id,'report_updated',
    jsonb_build_object('status_before',before_row.status,'status_after',p_status,'priority_before',before_row.priority,'priority_after',p_priority,
      'assigned_before',before_row.assigned_to,'assigned_after',p_assigned_to,'internal_notes_changed',before_row.internal_notes<>p_internal_notes,
      'resolution_changed',before_row.resolution<>p_resolution,'version',before_row.version+1));
  return jobrun_private.jr_admin_support_row(p_id);
end $$;

create function jobrun_private.jr_admin_question_reports(p_query text default '',p_resolved boolean default false,p_page integer default 1,p_page_size integer default 25) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare rows jsonb; total_count bigint;
begin
  perform jobrun_private.jr_require_admin();
  if p_query is null or length(p_query)>200 or p_resolved is null or p_page is null or p_page<1 or p_page>100000 or p_page_size is null or p_page_size not between 1 and 100 then
    raise exception 'invalid_input' using errcode='22023';
  end if;
  select count(*) into total_count from public.question_report r join auth.users u on u.id=r.user_id
    join public.question q on q.id=r.question_id
    where (r.resolved_at is not null)=p_resolved and (trim(p_query)='' or strpos(lower(concat_ws(' ',r.note,r.reason,u.email,q.key,r.id::text)),lower(trim(p_query)))>0);
  select coalesce(jsonb_agg(s.payload order by s.created_at desc,s.id),'[]'::jsonb) into rows from (
    select r.id,r.created_at,to_jsonb(r)||jsonb_build_object('reporter_email',u.email,'reporter_name',coalesce(p.display_name,''),
      'question_key',q.key,'question_title_he',coalesce(q.assets->'titles'->>'he',q.key),
      'question_title_en',coalesce(q.assets->'titles'->>'en',q.key)) as payload
      from public.question_report r join auth.users u on u.id=r.user_id left join public.user_profile p on p.id=u.id
      join public.question q on q.id=r.question_id
      where (r.resolved_at is not null)=p_resolved and (trim(p_query)='' or strpos(lower(concat_ws(' ',r.note,r.reason,u.email,q.key,r.id::text)),lower(trim(p_query)))>0)
      order by r.created_at desc,r.id limit p_page_size offset ((p_page-1)::bigint*p_page_size)) s;
  return jsonb_build_object('reports',rows,'total',total_count);
end $$;

create function jobrun_private.jr_admin_resolve_question_report(p_id uuid,p_resolved boolean) returns jsonb
language plpgsql security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_require_admin(); result jsonb;
begin
  if p_resolved is null then raise exception 'invalid_input' using errcode='22023'; end if;
  update public.question_report set resolved_at=case when p_resolved then now() else null end,
    resolved_by=case when p_resolved then caller::text else null end where id=p_id
    returning jsonb_build_object('id',id,'resolved_at',resolved_at,'resolved_by',resolved_by) into result;
  if result is null then raise exception 'report_unavailable' using errcode='22023'; end if;
  insert into public.jr_admin_events(actor_id,action,details) values(caller,'question_report_updated',jsonb_build_object('question_report_id',p_id,'resolved',p_resolved));
  return result;
end $$;

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('jr-support-files','jr-support-files',false,5242880,array['image/png','image/jpeg','image/webp','application/pdf','text/plain']);

-- These are the only storage-policy helpers clients may execute. Each checks
-- current Auth/DB authorization; no caller-supplied owner/admin flag is trusted.
create function jobrun_private.jr_can_read_support_file(p_path text) returns boolean
language plpgsql stable security definer set search_path='' as $$
declare caller uuid:=auth.uid();
begin
  return exists(select 1 from public.jr_support_files f join auth.users u on u.id=caller
    where f.storage_path=p_path and u.email_confirmed_at is not null and u.deleted_at is null
      and (f.owner_id=u.id or exists(select 1 from public.jr_members m where m.email=lower(u.email) and m.can_manage_tasks)));
end
$$;

create function jobrun_private.jr_can_upload_support_file(p_path text,p_metadata jsonb) returns boolean
language plpgsql stable security definer set search_path='' as $$
declare caller uuid:=auth.uid();
begin
  return exists(select 1 from public.jr_support_files f join public.jr_support_reports r on r.id=f.report_id
    join auth.users u on u.id=caller
    where f.storage_path=p_path and f.owner_id=u.id and r.reporter_id=u.id and r.status not in ('resolved','closed')
      and u.email_confirmed_at is not null and u.deleted_at is null
      and (p_metadata->>'mimetype' is null or p_metadata->>'mimetype'=f.mime_type)
      and (p_metadata->>'size' is null or p_metadata->>'size'=f.size_bytes::text));
end
$$;

create policy "support owner or founder downloads private files" on storage.objects for select to authenticated
  using(bucket_id='jr-support-files' and (select jobrun_private.jr_can_read_support_file(name)));
create policy "support owner uploads reserved file once" on storage.objects for insert to authenticated
  with check(bucket_id='jr-support-files' and (select jobrun_private.jr_can_upload_support_file(name,metadata)));
-- Deliberately no UPDATE/DELETE policy: upsert and replacement are unavailable.

create function jobrun_private.jr_check_support_storage() returns trigger
language plpgsql security definer set search_path='' as $$
declare entry public.jr_support_files%rowtype; report_status text; actual_size text; actual_mime text;
begin
  if tg_op='UPDATE' and old.bucket_id='jr-support-files' and (new.bucket_id<>old.bucket_id or new.name<>old.name) then
    raise exception 'support_file_immutable' using errcode='23514';
  end if;
  if new.bucket_id<>'jr-support-files' then return new; end if;
  select f.* into entry from public.jr_support_files f where f.storage_path=new.name;
  if not found then raise exception 'support_file_reservation_required' using errcode='23514'; end if;
  -- Storage persistence may use its internal role without auth.uid(). Ownership
  -- is enforced by the caller policy; this check validates the committed bytes.
  select status into report_status from public.jr_support_reports where id=entry.report_id for update;
  if not found or report_status in ('resolved','closed') then raise exception 'report_unavailable' using errcode='23514'; end if;
  -- Recheck after the parent lock: pending-reservation removal shares that lock.
  if not exists(select 1 from public.jr_support_files where id=entry.id and storage_path=new.name) then
    raise exception 'support_file_reservation_required' using errcode='23514';
  end if;
  actual_size:=new.metadata->>'size'; actual_mime:=new.metadata->>'mimetype';
  if actual_mime is not null and actual_mime<>entry.mime_type then raise exception 'support_file_type_mismatch' using errcode='23514'; end if;
  if actual_size is null then
    -- The Storage permission probe runs before upload and can have incomplete
    -- metadata. It has the real caller JWT. Actual persistence must carry size.
    if auth.uid() is null or auth.uid()<>entry.owner_id then raise exception 'support_file_size_required' using errcode='23514'; end if;
  elsif actual_size<>entry.size_bytes::text or actual_mime is distinct from entry.mime_type then
    raise exception 'support_file_size_or_type_mismatch' using errcode='23514';
  end if;
  return new;
end $$;
create trigger jr_support_storage_guard before insert or update of bucket_id,name,metadata
  on storage.objects for each row execute function jobrun_private.jr_check_support_storage();

-- Revoke PostgreSQL's default function EXECUTE before granting only the public
-- entry points and exact private targets. Internal helpers have no client grant.
revoke all on function jobrun_private.jr_verified_user() from public,anon,authenticated;
revoke all on function jobrun_private.jr_require_admin() from public,anon,authenticated;
revoke all on function jobrun_private.jr_admin_user_row(uuid) from public,anon,authenticated;
revoke all on function jobrun_private.jr_support_public_row(uuid) from public,anon,authenticated;
revoke all on function jobrun_private.jr_support_assignees() from public,anon,authenticated;
revoke all on function jobrun_private.jr_admin_support_row(uuid) from public,anon,authenticated;
revoke all on function jobrun_private.jr_check_support_storage() from public,anon,authenticated;

create function public.jr_admin_users(p_query text default '',p_page integer default 1,p_page_size integer default 25) returns jsonb
language sql security invoker set search_path='' begin atomic
  select jobrun_private.jr_admin_users(p_query,p_page,p_page_size);
end;
create function public.jr_admin_update_user(p_user_id uuid,p_plan_tier text,p_pilot_access boolean,p_expected_plan text,p_expected_access boolean) returns jsonb
language sql security invoker set search_path='' begin atomic
  select jobrun_private.jr_admin_update_user(p_user_id,p_plan_tier,p_pilot_access,p_expected_plan,p_expected_access);
end;
create function public.jr_submit_support_report(p_id uuid,p_subject text,p_description text,p_category text,p_language text,p_page_path text,p_question_key text default null) returns jsonb
language sql security invoker set search_path='' begin atomic
  select jobrun_private.jr_submit_support_report(p_id,p_subject,p_description,p_category,p_language,p_page_path,p_question_key);
end;
create function public.jr_reserve_support_file(p_id uuid,p_report_id uuid,p_name text,p_mime_type text,p_size_bytes bigint) returns jsonb
language sql security invoker set search_path='' begin atomic
  select jobrun_private.jr_reserve_support_file(p_id,p_report_id,p_name,p_mime_type,p_size_bytes);
end;
create function public.jr_remove_support_file(p_id uuid) returns boolean
language sql security invoker set search_path='' begin atomic
  select jobrun_private.jr_remove_support_file(p_id);
end;
create function public.jr_admin_support_list(p_query text default '',p_status text default 'all',p_page integer default 1,p_page_size integer default 25) returns jsonb
language sql security invoker set search_path='' begin atomic
  select jobrun_private.jr_admin_support_list(p_query,p_status,p_page,p_page_size);
end;
create function public.jr_admin_support_detail(p_id uuid) returns jsonb
language sql security invoker set search_path='' begin atomic
  select jobrun_private.jr_admin_support_detail(p_id);
end;
create function public.jr_admin_update_support(p_id uuid,p_expected_version integer,p_status text,p_priority text,p_assigned_to uuid,p_internal_notes text,p_resolution text) returns jsonb
language sql security invoker set search_path='' begin atomic
  select jobrun_private.jr_admin_update_support(p_id,p_expected_version,p_status,p_priority,p_assigned_to,p_internal_notes,p_resolution);
end;
create function public.jr_admin_question_reports(p_query text default '',p_resolved boolean default false,p_page integer default 1,p_page_size integer default 25) returns jsonb
language sql security invoker set search_path='' begin atomic
  select jobrun_private.jr_admin_question_reports(p_query,p_resolved,p_page,p_page_size);
end;
create function public.jr_admin_resolve_question_report(p_id uuid,p_resolved boolean) returns jsonb
language sql security invoker set search_path='' begin atomic
  select jobrun_private.jr_admin_resolve_question_report(p_id,p_resolved);
end;

do $$
declare signature text;
begin
  foreach signature in array array[
    'jr_admin_users(text,integer,integer)',
    'jr_admin_update_user(uuid,text,boolean,text,boolean)',
    'jr_submit_support_report(uuid,text,text,text,text,text,text)',
    'jr_reserve_support_file(uuid,uuid,text,text,bigint)',
    'jr_remove_support_file(uuid)',
    'jr_admin_support_list(text,text,integer,integer)',
    'jr_admin_support_detail(uuid)',
    'jr_admin_update_support(uuid,integer,text,text,uuid,text,text)',
    'jr_admin_question_reports(text,boolean,integer,integer)',
    'jr_admin_resolve_question_report(uuid,boolean)'
  ] loop
    execute 'revoke all on function public.'||signature||' from public,anon,authenticated';
    execute 'revoke all on function jobrun_private.'||signature||' from public,anon,authenticated';
    execute 'grant execute on function public.'||signature||' to authenticated';
    execute 'grant execute on function jobrun_private.'||signature||' to authenticated';
  end loop;
end $$;
revoke all on function jobrun_private.jr_can_read_support_file(text) from public,anon,authenticated;
revoke all on function jobrun_private.jr_can_upload_support_file(text,jsonb) from public,anon,authenticated;
grant execute on function jobrun_private.jr_can_read_support_file(text),jobrun_private.jr_can_upload_support_file(text,jsonb) to authenticated;

comment on table public.jr_support_reports is 'Private support tickets; reporter-safe columns only through RLS, internal notes only via guarded founder RPC.';
comment on table public.jr_support_files is 'Bounded immutable upload reservations; private Storage objects are checked against exact MIME/byte size.';
comment on table public.jr_admin_events is 'Server-generated founder/support audit history. Browser clients cannot insert, update or delete.';
