-- Additive application infrastructure. Does not replace the existing AI schema.
create schema if not exists jobrun_private;
revoke all on schema jobrun_private from public, anon, authenticated;

create table public.jr_members (
  email text primary key check (email=lower(email)),
  display_name text not null,
  created_at timestamptz not null default now()
);
alter table public.jr_members enable row level security;
revoke all on public.jr_members from anon, authenticated;
grant select on public.jr_members to authenticated;
create policy "member sees own access" on public.jr_members for select to authenticated
using (email=lower((select auth.jwt()->>'email')));

create table public.jr_tasks (
  id uuid primary key default gen_random_uuid(),
  title text not null check (length(trim(title)) between 1 and 240),
  description text not null default '' check (length(description)<=20000),
  status text not null default 'todo' check (status in ('todo','doing','blocked','done')),
  priority text not null default 'medium' check (priority in ('low','medium','high')),
  area text not null default 'מוצר' check (length(area)<=100),
  phase text not null default 'גרסה ראשונה' check (length(phase)<=100),
  assignees text[] not null default '{}' check (assignees <@ array['harel','shaked']),
  due_date date,
  subtasks jsonb not null default '[]' check (jsonb_typeof(subtasks)='array' and jsonb_array_length(subtasks)<=100),
  links jsonb not null default '[]' check (jsonb_typeof(links)='array' and jsonb_array_length(links)<=30),
  archived boolean not null default false,
  version integer not null default 1,
  created_by uuid references auth.users(id) on delete set null default auth.uid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.jr_tasks enable row level security;
revoke all on public.jr_tasks from anon, authenticated;
grant select,insert,update on public.jr_tasks to authenticated;
create policy "members read tasks" on public.jr_tasks for select to authenticated
using (exists(select 1 from public.jr_members));
create policy "members add tasks" on public.jr_tasks for insert to authenticated
with check (exists(select 1 from public.jr_members) and created_by=(select auth.uid()));
create policy "members edit tasks" on public.jr_tasks for update to authenticated
using (exists(select 1 from public.jr_members)) with check (exists(select 1 from public.jr_members));
create index jr_tasks_status_idx on public.jr_tasks(status,archived);
create index jr_tasks_created_by_idx on public.jr_tasks(created_by);

create table public.jr_comments (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.jr_tasks(id) on delete cascade,
  body text not null check(length(trim(body)) between 1 and 5000),
  author_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  created_at timestamptz not null default now()
);
alter table public.jr_comments enable row level security;
revoke all on public.jr_comments from anon,authenticated;
grant select,insert on public.jr_comments to authenticated;
create policy "members read comments" on public.jr_comments for select to authenticated using(exists(select 1 from public.jr_members));
create policy "members add own comments" on public.jr_comments for insert to authenticated with check(exists(select 1 from public.jr_members) and author_id=(select auth.uid()));
create index jr_comments_task_idx on public.jr_comments(task_id,created_at);
create index jr_comments_author_idx on public.jr_comments(author_id);

create table public.jr_task_events (
  id bigint generated always as identity primary key,
  task_id uuid not null references public.jr_tasks(id) on delete cascade,
  actor_id uuid references auth.users(id) on delete set null,
  version integer not null,
  snapshot jsonb not null,
  created_at timestamptz not null default now()
);
alter table public.jr_task_events enable row level security;
revoke all on public.jr_task_events from anon,authenticated;
grant select on public.jr_task_events to authenticated;
create policy "members read history" on public.jr_task_events for select to authenticated using(exists(select 1 from public.jr_members));
create index jr_events_task_idx on public.jr_task_events(task_id,created_at);
create index jr_events_actor_idx on public.jr_task_events(actor_id);

create function jobrun_private.version_task() returns trigger language plpgsql set search_path='' as $$
begin
  if new.id<>old.id or new.created_at<>old.created_at or new.created_by is distinct from old.created_by then
    raise exception 'Task identity cannot be changed';
  end if;
  new.version:=old.version+1; new.updated_at:=now(); return new;
end $$;
create trigger jr_task_version before update on public.jr_tasks for each row execute function jobrun_private.version_task();
-- A narrowly scoped trigger, not an exposed RPC. Clients cannot forge history.
create function jobrun_private.audit_task() returns trigger language plpgsql security definer set search_path='' as $$
begin
  if auth.uid() is null then return new; end if;
  insert into public.jr_task_events(task_id,actor_id,version,snapshot) values(new.id,auth.uid(),new.version,to_jsonb(new));
  return new;
end $$;
revoke all on function jobrun_private.audit_task() from public,anon,authenticated;
revoke all on function jobrun_private.version_task() from public,anon,authenticated;
create trigger jr_task_audit after insert or update on public.jr_tasks for each row execute function jobrun_private.audit_task();

create table public.jr_practice_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  question_id uuid not null references public.question(id) on delete cascade,
  answer text not null default '' check(length(answer)<=30000),
  self_rating integer check(self_rating between 1 and 3),
  completed boolean not null default false,
  bookmarked boolean not null default false,
  version integer not null default 1,
  updated_at timestamptz not null default now(),
  unique(user_id,question_id)
);
alter table public.jr_practice_entries enable row level security;
revoke all on public.jr_practice_entries from anon,authenticated;
grant select,insert,update on public.jr_practice_entries to authenticated;
create policy "read own practice" on public.jr_practice_entries for select to authenticated using(user_id=(select auth.uid()));
create policy "insert own practice" on public.jr_practice_entries for insert to authenticated with check(user_id=(select auth.uid()) and exists(select 1 from public.jr_members));
create policy "update own practice" on public.jr_practice_entries for update to authenticated using(user_id=(select auth.uid())) with check(user_id=(select auth.uid()) and exists(select 1 from public.jr_members));
create index jr_practice_question_idx on public.jr_practice_entries(question_id);
create function jobrun_private.version_practice() returns trigger language plpgsql set search_path='' as $$
begin
 if new.id<>old.id or new.user_id<>old.user_id or new.question_id<>old.question_id then raise exception 'Practice identity cannot be changed'; end if;
 new.version:=old.version+1; new.updated_at:=now(); return new;
end $$;
revoke all on function jobrun_private.version_practice() from public,anon,authenticated;
create trigger jr_practice_version before update on public.jr_practice_entries for each row execute function jobrun_private.version_practice();

-- Only explicitly allowlisted beta testers can access these unreviewed seeds.
grant select on public.question,public.question_translation to authenticated;
create policy "founders review example questions" on public.question for select to authenticated
using(exists(select 1 from public.jr_members) and assets->>'collection'='jobrun_example_v1' and status='in_review');
create policy "founders review example translations" on public.question_translation for select to authenticated
using(exists(select 1 from public.question q where q.id=question_id and q.assets->>'collection'='jobrun_example_v1'));

insert into public.jr_members(email,display_name) values('jobrunerai@gmail.com','JobRun');
insert into public.jr_tasks(title,description,status,priority,area,assignees) values
('לבדוק את משובי ה־AI עם מראיין מנוסה','לתעד דוגמאות, טעויות והצעות לשיפור. המשוב האוטומטי עדיין אינו מחובר לאתר.','doing','high','AI',array['shaked']),
('להעביר 30 שאלות דוגמה לביקורת מקצועית','לבדוק פתרונות, רמת קושי והתאמה בין עברית לאנגלית לפני פרסום לציבור.','todo','high','תוכן',array['harel','shaked']),
('לחבר פריסות אוטומטיות מ־GitHub','נדרשת הרשאת בעל המאגר BIGshak4 להתקנת Netlify. בינתיים הפריסה ידנית.','blocked','medium','תשתית',array['shaked']),
('לגייס משתמשים לפיילוט','לבחור סטודנטים ומועמדי ג׳וניור ולתעד משוב לאחר תרגול ראשון.','todo','medium','מוצר',array['harel']),
('להגדיר שירות מיילים לאימות משתמשים','בדיקת SMTP, כתובות החזרה ומסירת מיילים לשני המייסדים לפני הרחבת הפיילוט.','todo','high','תשתית',array['harel']);
