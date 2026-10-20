-- In-app updates and personal support history. Broadcasts occupy one row, not
-- one notification per account. Read receipts are sparse and owner-controlled.
-- All public payloads are authored plain text. No email delivery is configured.

create table public.jr_announcements (
  id uuid primary key,
  title_he text not null check(length(trim(title_he)) between 1 and 160),
  body_he text not null check(length(trim(body_he)) between 1 and 10000),
  title_en text check(length(trim(title_en)) between 1 and 160),
  body_en text check(length(trim(body_en)) between 1 and 10000),
  status text not null default 'draft' check(status in ('draft','published','archived')),
  version integer not null default 1,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check((title_en is null)=(body_en is null)),
  check((status='draft' and published_at is null) or (status='published' and published_at is not null) or status='archived')
);
create index jr_announcements_visible_idx on public.jr_announcements(published_at desc,id) where status='published';
alter table public.jr_announcements enable row level security;
revoke all on public.jr_announcements from public,anon,authenticated;

create table public.jr_announcement_reads (
  user_id uuid not null references auth.users(id) on delete cascade,
  announcement_id uuid not null references public.jr_announcements(id) on delete cascade,
  read_at timestamptz not null default now(),
  primary key(user_id,announcement_id)
);
create index jr_announcement_reads_announcement_idx on public.jr_announcement_reads(announcement_id);
alter table public.jr_announcement_reads enable row level security;
revoke all on public.jr_announcement_reads from public,anon,authenticated;

create table public.jr_support_updates (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references public.jr_support_reports(id) on delete cascade,
  recipient_id uuid not null references auth.users(id) on delete cascade,
  update_kind text not null check(update_kind in ('status','message')),
  body text not null check(length(trim(body)) between 1 and 5000),
  language text not null check(language in ('he','en')),
  status text not null check(status in ('open','in_progress','waiting','resolved','closed')),
  report_version integer not null,
  idempotency_id uuid unique,
  requested_status text,
  created_at timestamptz not null default now(),
  read_at timestamptz,
  unique(report_id,report_version)
);
create index jr_support_updates_owner_idx on public.jr_support_updates(recipient_id,created_at desc,id);
create index jr_support_updates_unread_idx on public.jr_support_updates(recipient_id) where read_at is null;
create index jr_support_updates_report_idx on public.jr_support_updates(report_id,created_at,id);
alter table public.jr_support_updates enable row level security;
revoke all on public.jr_support_updates from public,anon,authenticated;

-- Existing support receipts and direct owner reads must not reveal a founder's
-- identity or workflow. Original issue context and public resolution remain.
revoke select(assigned_to,priority) on public.jr_support_reports from authenticated;
create or replace function jobrun_private.jr_support_public_row(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
  select jsonb_build_object('id',r.id,'subject',r.subject,'description',r.description,'category',r.category,
    'language',r.language,'page_path',r.page_path,'question_key',r.question_key,'status',r.status,
    'resolution',r.resolution,'created_at',r.created_at,'updated_at',r.updated_at,
    'unread_count',(select count(*) from public.jr_support_updates s where s.report_id=r.id and s.read_at is null))
  from public.jr_support_reports r where r.id=p_id;
$$;

create function jobrun_private.jr_support_update_row(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
  select jsonb_build_object('id',s.id,'kind','support','title',case when s.language='he' then 'עדכון בפנייה שלכם' else 'Your support request was updated' end,
    'body',s.body,'language',s.language,'report_id',s.report_id,'status',s.status,'created_at',s.created_at,'read_at',s.read_at)
  from public.jr_support_updates s where s.id=p_id;
$$;

create or replace function jobrun_private.jr_submit_support_report(p_id uuid,p_subject text,p_description text,p_category text,p_language text,p_page_path text,p_question_key text default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_verified_user(); existing public.jr_support_reports%rowtype;
begin
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
    raise exception 'invalid_input' using errcode='22023'; end if;
  if (select count(*) from public.jr_support_reports where reporter_id=caller and created_at>now()-interval '24 hours')>=5 then
    raise exception 'support_rate_limit' using errcode='23514'; end if;
  insert into public.jr_support_reports(id,reporter_id,subject,description,category,language,page_path,question_key)
    values(p_id,caller,trim(p_subject),trim(p_description),p_category,p_language,p_page_path,nullif(trim(p_question_key),''));
  insert into public.jr_support_updates(report_id,recipient_id,update_kind,body,language,status,report_version)
    values(p_id,caller,'status',case when p_language='he' then 'הפנייה שלכם התקבלה. נעדכן כאן כשיהיה שינוי או מענה.'
      else 'Your support request was received. Updates and replies will appear here.' end,p_language,'open',1);
  insert into public.jr_admin_events(actor_id,report_id,action) values(caller,p_id,'report_created');
  return jobrun_private.jr_support_public_row(p_id);
end $$;

create function jobrun_private.jr_user_inbox(p_kind text default 'all',p_page integer default 1,p_page_size integer default 25,p_language text default 'he') returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_verified_user(); rows jsonb; total_count bigint; unread bigint;
begin
  if p_kind is null or p_kind not in ('all','announcement','support') or p_page is null or p_page not between 1 and 100000
    or p_page_size is null or p_page_size not between 1 and 100 or p_language is null or p_language not in ('he','en') then
    raise exception 'invalid_input' using errcode='22023';
  end if;
  select (select count(*) from public.jr_announcements a where a.status='published' and not exists(
      select 1 from public.jr_announcement_reads r where r.announcement_id=a.id and r.user_id=caller))
    +(select count(*) from public.jr_support_updates s where s.recipient_id=caller and s.read_at is null) into unread;
  select (case when p_kind in ('all','announcement') then (select count(*) from public.jr_announcements where status='published') else 0 end)
    +(case when p_kind in ('all','support') then (select count(*) from public.jr_support_updates where recipient_id=caller) else 0 end) into total_count;
  select coalesce(jsonb_agg(t.payload order by t.created_at desc,t.id),'[]'::jsonb) into rows from (
    select combined.* from (
      select a.id,a.published_at as created_at,jsonb_build_object('id',a.id,'kind','announcement',
        'title',case when p_language='en' and a.title_en is not null then a.title_en else a.title_he end,
        'body',case when p_language='en' and a.body_en is not null then a.body_en else a.body_he end,
        'language',case when p_language='en' and a.title_en is not null then 'en' else 'he' end,
        'created_at',a.published_at,'read_at',r.read_at) as payload
      from public.jr_announcements a left join public.jr_announcement_reads r on r.announcement_id=a.id and r.user_id=caller
      where a.status='published' and p_kind in ('all','announcement')
      union all
      select s.id,s.created_at,jobrun_private.jr_support_update_row(s.id) from public.jr_support_updates s
      where s.recipient_id=caller and p_kind in ('all','support')
    ) combined order by created_at desc,id limit p_page_size offset((p_page-1)::bigint*p_page_size)
  ) t;
  return jsonb_build_object('items',rows,'total',total_count,'unread_count',unread);
end $$;

create function jobrun_private.jr_mark_inbox_read(p_kind text,p_id uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_verified_user(); seen_at timestamptz;
begin
  if p_kind is null or p_kind not in ('announcement','support') or p_id is null then raise exception 'invalid_input' using errcode='22023'; end if;
  if p_kind='announcement' then
    if not exists(select 1 from public.jr_announcements where id=p_id and status='published') then
      raise exception 'inbox_item_unavailable' using errcode='42501';
    end if;
    insert into public.jr_announcement_reads(user_id,announcement_id) values(caller,p_id) on conflict do nothing;
    select read_at into seen_at from public.jr_announcement_reads where user_id=caller and announcement_id=p_id;
  else
    update public.jr_support_updates set read_at=coalesce(read_at,now()) where id=p_id and recipient_id=caller returning read_at into seen_at;
    if not found then raise exception 'inbox_item_unavailable' using errcode='42501'; end if;
  end if;
  return jsonb_build_object('kind',p_kind,'id',p_id,'read_at',seen_at);
end $$;

create function jobrun_private.jr_mark_all_inbox_read() returns jsonb
language plpgsql security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_verified_user(); marked bigint;
begin
  -- One statement snapshot: a support message or broadcast committed while
  -- this action is running must remain unread for the user's next visit.
  with announcement_receipts as (
    insert into public.jr_announcement_reads(user_id,announcement_id)
      select caller,id from public.jr_announcements where status='published' on conflict do nothing
      returning 1
  ), support_receipts as (
    update public.jr_support_updates set read_at=now() where recipient_id=caller and read_at is null
      returning 1
  ) select (select count(*) from announcement_receipts)+(select count(*) from support_receipts) into marked;
  return jsonb_build_object('marked',marked);
end $$;

create function jobrun_private.jr_my_support_reports(p_page integer default 1,p_page_size integer default 25) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_verified_user(); rows jsonb; total_count bigint;
begin
  if p_page is null or p_page not between 1 and 100000 or p_page_size is null or p_page_size not between 1 and 100 then
    raise exception 'invalid_input' using errcode='22023';
  end if;
  select count(*) into total_count from public.jr_support_reports where reporter_id=caller;
  select coalesce(jsonb_agg(jobrun_private.jr_support_public_row(s.id) order by s.created_at desc,s.id),'[]'::jsonb) into rows
    from(select id,created_at from public.jr_support_reports where reporter_id=caller order by created_at desc,id limit p_page_size offset((p_page-1)::bigint*p_page_size)) s;
  return jsonb_build_object('reports',rows,'total',total_count);
end $$;

create function jobrun_private.jr_my_support_detail(p_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_verified_user(); files jsonb; updates jsonb;
begin
  if not exists(select 1 from public.jr_support_reports where id=p_id and reporter_id=caller) then
    raise exception 'report_unavailable' using errcode='42501';
  end if;
  select coalesce(jsonb_agg(jsonb_build_object('id',f.id,'report_id',f.report_id,'storage_path',f.storage_path,'name',f.name,
    'mime_type',f.mime_type,'size_bytes',f.size_bytes,'created_at',f.created_at,'uploaded',o.id is not null) order by f.created_at,f.id),'[]'::jsonb)
    into files from public.jr_support_files f left join storage.objects o on o.bucket_id='jr-support-files' and o.name=f.storage_path where f.report_id=p_id;
  select coalesce(jsonb_agg(jobrun_private.jr_support_update_row(s.id) order by s.created_at,s.id),'[]'::jsonb)
    into updates from public.jr_support_updates s where s.report_id=p_id and s.recipient_id=caller;
  return jsonb_build_object('report',jobrun_private.jr_support_public_row(p_id),'files',files,'updates',updates);
end $$;

create function jobrun_private.jr_admin_announcements(p_query text default '',p_status text default 'all',p_page integer default 1,p_page_size integer default 25) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare rows jsonb; total_count bigint;
begin
  perform jobrun_private.jr_require_admin();
  if p_query is null or length(p_query)>200 or p_status is null or p_status not in ('all','draft','published','archived') or p_page is null or p_page not between 1 and 100000
    or p_page_size is null or p_page_size not between 1 and 100 then raise exception 'invalid_input' using errcode='22023'; end if;
  select count(*) into total_count from public.jr_announcements a where (p_status='all' or a.status=p_status)
    and (trim(p_query)='' or strpos(lower(concat_ws(' ',a.id::text,a.title_he,a.body_he,a.title_en,a.body_en)),lower(trim(p_query)))>0);
  select coalesce(jsonb_agg(to_jsonb(s) order by s.created_at desc,s.id),'[]'::jsonb) into rows from(
    select * from public.jr_announcements a where (p_status='all' or a.status=p_status)
      and (trim(p_query)='' or strpos(lower(concat_ws(' ',a.id::text,a.title_he,a.body_he,a.title_en,a.body_en)),lower(trim(p_query)))>0)
      order by a.created_at desc,a.id limit p_page_size offset((p_page-1)::bigint*p_page_size)) s;
  return jsonb_build_object('announcements',rows,'total',total_count);
end $$;

create function jobrun_private.jr_admin_save_announcement(p_id uuid,p_expected_version integer,p_title_he text default null,p_body_he text default null,p_title_en text default null,p_body_en text default null,p_action text default 'save') returns jsonb
language plpgsql security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_require_admin(); before_row public.jr_announcements%rowtype; result public.jr_announcements%rowtype;
  english_title text:=nullif(trim(p_title_en),''); english_body text:=nullif(trim(p_body_en),'');
begin
  if p_id is null or p_expected_version is null or p_expected_version<0 or p_action is null or p_action not in ('save','publish','archive') then raise exception 'invalid_input' using errcode='22023'; end if;
  -- Client-generated IDs are also the recovery key after an uncertain create.
  -- Serialize first creation so concurrent identical IDs get PT409, not 23505.
  perform pg_advisory_xact_lock(hashtextextended('jr_announcement:'||p_id::text,0));
  select * into before_row from public.jr_announcements where id=p_id for update;
  if found then
    if before_row.version<>p_expected_version then raise exception 'conflict_reload' using errcode='PT409'; end if;
    if before_row.status<>'draft' and p_action<>'archive' then raise exception 'announcement_immutable' using errcode='22023'; end if;
    if before_row.status='archived' then raise exception 'announcement_immutable' using errcode='22023'; end if;
  elsif p_expected_version<>0 or p_action='archive' then raise exception 'conflict_reload' using errcode='PT409'; end if;
  if p_action<>'archive' and (p_title_he is null or length(trim(p_title_he)) not between 1 and 160
    or p_body_he is null or length(trim(p_body_he)) not between 1 and 10000
    or (english_title is null)<>(english_body is null) or length(english_title)>160 or length(english_body)>10000) then
    raise exception 'invalid_input' using errcode='22023';
  end if;
  if before_row.id is null then
    insert into public.jr_announcements(id,title_he,body_he,title_en,body_en,status,published_at)
      values(p_id,trim(p_title_he),trim(p_body_he),english_title,english_body,
        case when p_action='publish' then 'published' else 'draft' end,case when p_action='publish' then now() end) returning * into result;
  elsif p_action='archive' then
    update public.jr_announcements set status='archived',version=version+1,updated_at=now() where id=p_id returning * into result;
  else
    update public.jr_announcements set title_he=trim(p_title_he),body_he=trim(p_body_he),title_en=english_title,body_en=english_body,
      status=case when p_action='publish' then 'published' else 'draft' end,
      published_at=case when p_action='publish' then now() end,version=version+1,updated_at=now() where id=p_id returning * into result;
  end if;
  insert into public.jr_admin_events(actor_id,action,details) values(caller,'announcement_'||p_action,
    jsonb_build_object('announcement_id',p_id,'status',result.status,'version',result.version));
  return to_jsonb(result);
end $$;

create function jobrun_private.jr_immutable_published_announcement() returns trigger
language plpgsql set search_path='' as $$
begin
  if old.status<>'draft' and (new.title_he<>old.title_he or new.body_he<>old.body_he or new.title_en is distinct from old.title_en
    or new.body_en is distinct from old.body_en or new.published_at is distinct from old.published_at) then
    raise exception 'announcement_immutable' using errcode='22023';
  end if;
  if (old.status='archived' and new.status<>'archived') or (old.status='published' and new.status='draft') then
    raise exception 'announcement_immutable' using errcode='22023';
  end if;
  return new;
end $$;
create trigger jr_announcement_immutable before update on public.jr_announcements for each row execute function jobrun_private.jr_immutable_published_announcement();

-- Preserve the original RPC signature and private internal workflow; publish
-- only explicit status/resolution changes to a separate, minimal timeline.
create or replace function jobrun_private.jr_admin_update_support(p_id uuid,p_expected_version integer,p_status text,p_priority text,p_assigned_to uuid,p_internal_notes text,p_resolution text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_require_admin(); before_row public.jr_support_reports%rowtype; public_body text;
begin
  if p_expected_version is null or p_status is null or p_status not in ('open','in_progress','waiting','resolved','closed')
    or p_priority is null or p_priority not in ('low','normal','high') or p_internal_notes is null or length(p_internal_notes)>10000
    or p_resolution is null or length(p_resolution)>5000 then raise exception 'invalid_input' using errcode='22023'; end if;
  if p_assigned_to is not null and not exists(select 1 from auth.users u join public.jr_members m on m.email=lower(u.email)
    where u.id=p_assigned_to and m.can_manage_tasks and u.email_confirmed_at is not null and u.deleted_at is null) then
    raise exception 'invalid_assignee' using errcode='22023'; end if;
  select * into before_row from public.jr_support_reports where id=p_id for update;
  if not found then raise exception 'report_unavailable' using errcode='22023'; end if;
  if before_row.version<>p_expected_version then raise exception 'conflict_reload' using errcode='PT409'; end if;
  if p_status in ('resolved','closed') and length(trim(p_resolution))=0 then
    raise exception 'public_resolution_required' using errcode='22023'; end if;
  update public.jr_support_reports set status=p_status,priority=p_priority,assigned_to=p_assigned_to,
    internal_notes=p_internal_notes,resolution=trim(p_resolution),version=version+1,updated_at=now() where id=p_id;
  if before_row.status<>p_status or before_row.resolution<>trim(p_resolution) then
    public_body:=case when p_status in ('resolved','closed') or (before_row.resolution<>trim(p_resolution) and trim(p_resolution)<>'') then trim(p_resolution)
      when before_row.language='he' then 'מצב הפנייה שלכם עודכן.' else 'The status of your support request was updated.' end;
    insert into public.jr_support_updates(report_id,recipient_id,update_kind,body,language,status,report_version)
      values(p_id,before_row.reporter_id,'status',public_body,before_row.language,p_status,before_row.version+1);
  end if;
  insert into public.jr_admin_events(actor_id,report_id,action,details) values(caller,p_id,'report_updated',
    jsonb_build_object('status_before',before_row.status,'status_after',p_status,'priority_before',before_row.priority,'priority_after',p_priority,
      'assigned_before',before_row.assigned_to,'assigned_after',p_assigned_to,'internal_notes_changed',before_row.internal_notes<>p_internal_notes,
      'resolution_changed',before_row.resolution<>trim(p_resolution),'version',before_row.version+1));
  return jobrun_private.jr_admin_support_row(p_id);
end $$;

create function jobrun_private.jr_admin_reply_support(p_report_id uuid,p_expected_version integer,p_idempotency_id uuid,p_message text,p_status text default null,p_language text default 'he') returns jsonb
language plpgsql security definer set search_path='' as $$
declare caller uuid:=jobrun_private.jr_require_admin(); report public.jr_support_reports%rowtype;
  existing public.jr_support_updates%rowtype; next_status text; result_id uuid;
begin
  if p_report_id is null or p_expected_version is null or p_idempotency_id is null or p_message is null or length(trim(p_message)) not between 1 and 5000
    or (p_status is not null and p_status not in ('open','in_progress','waiting','resolved','closed'))
    or p_language is null or p_language not in ('he','en') then raise exception 'invalid_input' using errcode='22023'; end if;
  perform pg_advisory_xact_lock(hashtextextended('jr_support_reply:'||p_idempotency_id::text,0));
  select * into report from public.jr_support_reports where id=p_report_id for update;
  if not found then raise exception 'report_unavailable' using errcode='22023'; end if;
  select * into existing from public.jr_support_updates where idempotency_id=p_idempotency_id;
  if found then
    if existing.report_id<>p_report_id or existing.body<>trim(p_message) or existing.requested_status is distinct from p_status or existing.language<>p_language then
      raise exception 'idempotency_conflict' using errcode='PT409'; end if;
    return jsonb_build_object('report',jobrun_private.jr_admin_support_row(p_report_id),'update',jobrun_private.jr_support_update_row(existing.id));
  end if;
  if report.version<>p_expected_version then raise exception 'conflict_reload' using errcode='PT409'; end if;
  next_status:=coalesce(p_status,report.status);
  update public.jr_support_reports set status=next_status,
    resolution=case when p_status in ('resolved','closed') then trim(p_message) else resolution end,
    version=version+1,updated_at=now() where id=p_report_id;
  insert into public.jr_support_updates(report_id,recipient_id,update_kind,body,language,status,report_version,idempotency_id,requested_status)
    values(p_report_id,report.reporter_id,'message',trim(p_message),p_language,next_status,report.version+1,p_idempotency_id,p_status) returning id into result_id;
  insert into public.jr_admin_events(actor_id,report_id,action,details) values(caller,p_report_id,'support_public_reply',
    jsonb_build_object('public_update_id',result_id,'status_before',report.status,'status_after',next_status,'version',report.version+1));
  return jsonb_build_object('report',jobrun_private.jr_admin_support_row(p_report_id),'update',jobrun_private.jr_support_update_row(result_id));
end $$;

create or replace function jobrun_private.jr_admin_support_detail(p_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare report jsonb; files jsonb; events jsonb; updates jsonb;
begin
  perform jobrun_private.jr_require_admin();
  report:=jobrun_private.jr_admin_support_row(p_id);
  if report is null then raise exception 'report_unavailable' using errcode='22023'; end if;
  select coalesce(jsonb_agg(to_jsonb(f)||jsonb_build_object('uploaded',o.id is not null) order by f.created_at,f.id),'[]'::jsonb)
    into files from public.jr_support_files f left join storage.objects o on o.bucket_id='jr-support-files' and o.name=f.storage_path where f.report_id=p_id;
  select coalesce(jsonb_agg(to_jsonb(e)||jsonb_build_object('actor_email',u.email) order by e.created_at desc,e.id desc),'[]'::jsonb)
    into events from public.jr_admin_events e left join auth.users u on u.id=e.actor_id where e.report_id=p_id;
  select coalesce(jsonb_agg(jobrun_private.jr_support_update_row(s.id) order by s.created_at,s.id),'[]'::jsonb)
    into updates from public.jr_support_updates s where s.report_id=p_id;
  return jsonb_build_object('report',report,'files',files,'events',events,'assignees',jobrun_private.jr_support_assignees(),'updates',updates);
end $$;

revoke all on function jobrun_private.jr_support_update_row(uuid),jobrun_private.jr_immutable_published_announcement() from public,anon,authenticated;

create function public.jr_user_inbox(p_kind text default 'all',p_page integer default 1,p_page_size integer default 25,p_language text default 'he') returns jsonb
language sql security invoker set search_path='' begin atomic select jobrun_private.jr_user_inbox(p_kind,p_page,p_page_size,p_language); end;
create function public.jr_mark_inbox_read(p_kind text,p_id uuid) returns jsonb
language sql security invoker set search_path='' begin atomic select jobrun_private.jr_mark_inbox_read(p_kind,p_id); end;
create function public.jr_mark_all_inbox_read() returns jsonb
language sql security invoker set search_path='' begin atomic select jobrun_private.jr_mark_all_inbox_read(); end;
create function public.jr_my_support_reports(p_page integer default 1,p_page_size integer default 25) returns jsonb
language sql security invoker set search_path='' begin atomic select jobrun_private.jr_my_support_reports(p_page,p_page_size); end;
create function public.jr_my_support_detail(p_id uuid) returns jsonb
language sql security invoker set search_path='' begin atomic select jobrun_private.jr_my_support_detail(p_id); end;
create function public.jr_admin_announcements(p_query text default '',p_status text default 'all',p_page integer default 1,p_page_size integer default 25) returns jsonb
language sql security invoker set search_path='' begin atomic select jobrun_private.jr_admin_announcements(p_query,p_status,p_page,p_page_size); end;
create function public.jr_admin_save_announcement(p_id uuid,p_expected_version integer,p_title_he text default null,p_body_he text default null,p_title_en text default null,p_body_en text default null,p_action text default 'save') returns jsonb
language sql security invoker set search_path='' begin atomic select jobrun_private.jr_admin_save_announcement(p_id,p_expected_version,p_title_he,p_body_he,p_title_en,p_body_en,p_action); end;
create function public.jr_admin_reply_support(p_report_id uuid,p_expected_version integer,p_idempotency_id uuid,p_message text,p_status text default null,p_language text default 'he') returns jsonb
language sql security invoker set search_path='' begin atomic select jobrun_private.jr_admin_reply_support(p_report_id,p_expected_version,p_idempotency_id,p_message,p_status,p_language); end;

do $$
declare signature text;
begin
  foreach signature in array array[
    'jr_user_inbox(text,integer,integer,text)','jr_mark_inbox_read(text,uuid)','jr_mark_all_inbox_read()',
    'jr_my_support_reports(integer,integer)','jr_my_support_detail(uuid)','jr_admin_announcements(text,text,integer,integer)',
    'jr_admin_save_announcement(uuid,integer,text,text,text,text,text)','jr_admin_reply_support(uuid,integer,uuid,text,text,text)'
  ] loop
    execute 'revoke all on function public.'||signature||' from public,anon,authenticated';
    execute 'revoke all on function jobrun_private.'||signature||' from public,anon,authenticated';
    execute 'grant execute on function public.'||signature||' to authenticated';
    execute 'grant execute on function jobrun_private.'||signature||' to authenticated';
  end loop;
end $$;

comment on table public.jr_announcements is 'Single immutable published bilingual broadcast, with no per-user notification fanout.';
comment on table public.jr_announcement_reads is 'Sparse per-owner read receipts, created only by authenticated read actions.';
comment on table public.jr_support_updates is 'Minimal public status/message snapshots for one report owner. No internal notes, admin identity or audit payload.';
