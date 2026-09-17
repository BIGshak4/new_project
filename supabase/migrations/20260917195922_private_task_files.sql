insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('jobrun-task-files','jobrun-task-files',false,10485760,array['application/pdf','image/png','image/jpeg','text/plain']);
create policy "founders read task files" on storage.objects for select to authenticated
using(bucket_id='jobrun-task-files' and exists(select 1 from public.jr_members where can_manage_tasks));
create policy "founders upload task files" on storage.objects for insert to authenticated
with check(bucket_id='jobrun-task-files' and exists(select 1 from public.jr_members where can_manage_tasks)
and exists(select 1 from public.jr_tasks t where t.id::text=(storage.foldername(name))[1]));
create policy "founders delete task files" on storage.objects for delete to authenticated
using(bucket_id='jobrun-task-files' and exists(select 1 from public.jr_members where can_manage_tasks));
