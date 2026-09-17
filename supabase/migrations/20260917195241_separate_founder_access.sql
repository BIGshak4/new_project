alter table public.jr_members add column can_manage_tasks boolean not null default false;
update public.jr_members set can_manage_tasks=true where email='jobrunerai@gmail.com';
alter policy "members read tasks" on public.jr_tasks using (exists(select 1 from public.jr_members where can_manage_tasks));
alter policy "members add tasks" on public.jr_tasks with check (exists(select 1 from public.jr_members where can_manage_tasks) and created_by=(select auth.uid()));
alter policy "members edit tasks" on public.jr_tasks using (exists(select 1 from public.jr_members where can_manage_tasks)) with check (exists(select 1 from public.jr_members where can_manage_tasks));
alter policy "members read comments" on public.jr_comments using (exists(select 1 from public.jr_members where can_manage_tasks));
alter policy "members add own comments" on public.jr_comments with check (exists(select 1 from public.jr_members where can_manage_tasks) and author_id=(select auth.uid()));
alter policy "members read history" on public.jr_task_events using (exists(select 1 from public.jr_members where can_manage_tasks));
-- Platform event trigger should not be callable through the public RPC API.
revoke execute on function public.rls_auto_enable() from public, anon, authenticated;
