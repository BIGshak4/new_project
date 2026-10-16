"""Execute the real quota trigger against synthetic, rollback-only SQL fixtures.

Opt in with SECURITY_STORAGE_FIXTURE_URL. The production migration is reused
verbatim except for schema/table/function names redirected into pg_temp. No real
parent, user, storage object, or file is read or modified. This validates SQL
behavior without claiming end-to-end compatibility with the Storage HTTP API.

The same storage_quota_fixture_sql() script can be run through Supabase MCP when
the developer's database password is unavailable. Assertions raise on failure;
ROLLBACK removes all fixture functions/tables, then a final SELECT reports success.
"""

from __future__ import annotations

import os
from pathlib import Path

import asyncpg
import pytest

MIGRATION = Path(__file__).resolve().parents[2] / "supabase/migrations/20261016171110_bound_answer_image_storage_quota.sql"


def storage_quota_fixture_sql() -> str:
    source = MIGRATION.read_text(encoding="utf-8")
    function_start = source.index("create or replace function jobrun_private.limit_answer_images()")
    function_end = source.index("end $$;", function_start) + len("end $$;")
    function = source[function_start:function_end]
    function = function.replace("jobrun_private.limit_answer_images", "pg_temp.limit_answer_images")
    function = function.replace("public.attempt", "pg_temp.quota_attempt")
    function = function.replace("public.interview_session", "pg_temp.quota_session")
    function = function.replace("storage.objects", "pg_temp.quota_objects")
    return """
begin;
set local statement_timeout = '15s';
set local lock_timeout = '2s';
select set_config('request.jwt.claims', '{}', true);
create temp table quota_attempt (
  id uuid primary key, user_id uuid not null, submitted_at timestamptz
) on commit drop;
create temp table quota_session (
  id uuid primary key, user_id uuid not null, status text not null
) on commit drop;
create temp table quota_objects (
  id uuid primary key default gen_random_uuid(), bucket_id text not null,
  name text not null, metadata jsonb, unique(bucket_id, name)
) on commit drop;
create temp table quota_results (case_name text primary key) on commit drop;
""" + function + """
create trigger fixture_image_limit before insert or update of bucket_id, name
  on pg_temp.quota_objects for each row execute function pg_temp.limit_answer_images();
create function pg_temp.image_path(owner_id uuid, parent_id uuid, serial integer) returns text
language sql immutable set search_path = '' as $$
  select owner_id::text || '/' || parent_id::text || '/' || (md5(serial::text)::uuid)::text || '.jpg';
$$;
create function pg_temp.expect_quota_rejection(statement text, case_name text) returns void
language plpgsql set search_path = '' as $$
begin
  begin
    execute statement;
  exception when check_violation then
    insert into pg_temp.quota_results values (case_name);
    return;
  end;
  raise exception 'Expected quota rejection: %', case_name;
end $$;
insert into pg_temp.quota_attempt(id,user_id,submitted_at) values
  ('11111111-1111-1111-1111-111111111111','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',null),
  ('22222222-2222-2222-2222-222222222222','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',now()),
  ('33333333-3333-3333-3333-333333333333','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',null),
  ('44444444-4444-4444-4444-444444444444','bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',null);
insert into pg_temp.quota_session(id,user_id,status) values
  ('55555555-5555-5555-5555-555555555555','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','in_progress'),
  ('66666666-6666-6666-6666-666666666666','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','paused');

-- Storage's persistence step need not carry an Auth subject.
do $$ begin
  if auth.uid() is not null then raise exception 'fixture must not have an Auth subject'; end if;
end $$;
insert into pg_temp.quota_results values ('no_auth_subject_required');

insert into pg_temp.quota_objects(bucket_id,name)
select 'practice-answer-images',pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '11111111-1111-1111-1111-111111111111',n) from generate_series(1,24) n;
do $$ begin
  if (select count(*) from pg_temp.quota_objects) <> 24 then raise exception '24 legitimate attempt images failed'; end if;
end $$;
insert into pg_temp.quota_results values ('attempt_accepts_24');
select pg_temp.expect_quota_rejection($q$
  insert into pg_temp.quota_objects(bucket_id,name) values ('practice-answer-images',
  pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','11111111-1111-1111-1111-111111111111',25))
$q$, 'attempt_rejects_25');

update pg_temp.quota_objects set name=pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '11111111-1111-1111-1111-111111111111',100) where name=pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '11111111-1111-1111-1111-111111111111',1);
insert into pg_temp.quota_results values ('rename_at_capacity_excludes_replaced_object');

select pg_temp.expect_quota_rejection($q$
  insert into pg_temp.quota_objects(bucket_id,name) values ('practice-answer-images',
  pg_temp.image_path('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','11111111-1111-1111-1111-111111111111',1))
$q$, 'rejects_forged_path_owner');
select pg_temp.expect_quota_rejection($q$
  insert into pg_temp.quota_objects(bucket_id,name) values ('practice-answer-images',
  pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','99999999-9999-9999-9999-999999999999',1))
$q$, 'rejects_missing_parent');
select pg_temp.expect_quota_rejection($q$
  insert into pg_temp.quota_objects(bucket_id,name) values ('practice-answer-images',
  pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','22222222-2222-2222-2222-222222222222',1))
$q$, 'rejects_closed_attempt');
select pg_temp.expect_quota_rejection($q$
  insert into pg_temp.quota_objects(bucket_id,name) values ('practice-answer-images',
  pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','66666666-6666-6666-6666-666666666666',1))
$q$, 'rejects_paused_interview');
select pg_temp.expect_quota_rejection($q$
  insert into pg_temp.quota_objects(bucket_id,name) values ('practice-answer-images','not/a/valid/path.jpg')
$q$, 'rejects_invalid_locator');
select pg_temp.expect_quota_rejection($q$
  insert into pg_temp.quota_objects(bucket_id,name) values ('practice-answer-images',
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/33333333-3333-3333-3333-333333333333/11111111-1111-1111-1111-111111111111.svg')
$q$, 'rejects_active_content_extension');

insert into pg_temp.quota_objects(bucket_id,name) values ('practice-answer-images',
  pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','33333333-3333-3333-3333-333333333333',1));
insert into pg_temp.quota_results values ('quota_is_per_parent');
select pg_temp.expect_quota_rejection($q$
  update pg_temp.quota_objects set name=pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '11111111-1111-1111-1111-111111111111',201) where name=pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '33333333-3333-3333-3333-333333333333',1)
$q$, 'rename_cannot_bypass_full_destination');

insert into pg_temp.quota_objects(bucket_id,name) values ('unrelated-bucket','unrestricted-other-object');
insert into pg_temp.quota_results values ('unrelated_buckets_unchanged');
select pg_temp.expect_quota_rejection($q$
  update pg_temp.quota_objects set bucket_id='practice-answer-images',
  name=pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','11111111-1111-1111-1111-111111111111',300)
  where bucket_id='unrelated-bucket'
$q$, 'bucket_move_cannot_bypass_full_destination');
update pg_temp.quota_objects set bucket_id='practice-answer-images',
  name=pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','33333333-3333-3333-3333-333333333333',300)
  where bucket_id='unrelated-bucket';
insert into pg_temp.quota_results values ('bucket_move_into_open_parent_validated');

insert into pg_temp.quota_objects(bucket_id,name)
select 'practice-answer-images',pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '55555555-5555-5555-5555-555555555555',n) from generate_series(1,200) n;
insert into pg_temp.quota_results values ('interview_accepts_200_including_more_than_24');
select pg_temp.expect_quota_rejection($q$
  insert into pg_temp.quota_objects(bucket_id,name) values ('practice-answer-images',
  pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','55555555-5555-5555-5555-555555555555',201))
$q$, 'interview_rejects_201');

-- Storage may finalize metadata without changing the locator after submission.
update pg_temp.quota_attempt set submitted_at=now() where id='11111111-1111-1111-1111-111111111111';
update pg_temp.quota_objects set name=name, metadata='{"size":123}' where name=pg_temp.image_path(
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','11111111-1111-1111-1111-111111111111',2);
insert into pg_temp.quota_results values ('unchanged_locator_metadata_update_preserved');
select pg_temp.expect_quota_rejection($q$
  update pg_temp.quota_objects set name=pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '11111111-1111-1111-1111-111111111111',500) where name=pg_temp.image_path('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '11111111-1111-1111-1111-111111111111',2)
$q$, 'closed_parent_cannot_accept_renamed_object');
do $$ begin
  if (select count(*) from pg_temp.quota_results) <> 19 then raise exception 'Expected 19 fixture assertions'; end if;
end $$;
rollback;
select 'passed' as storage_quota_fixture, 19 as assertions,
  to_regclass('pg_temp.quota_objects') is null as rolled_back;
"""


@pytest.mark.skipif(not os.environ.get("SECURITY_STORAGE_FIXTURE_URL"), reason="SECURITY_STORAGE_FIXTURE_URL not explicitly set")
async def test_storage_quota_with_rollback_only_synthetic_fixtures():
    url = os.environ["SECURITY_STORAGE_FIXTURE_URL"].replace("postgresql+asyncpg://", "postgresql://", 1)
    connection = await asyncpg.connect(url, timeout=15, statement_cache_size=0)
    try:
        await connection.execute(storage_quota_fixture_sql())
        assert await connection.fetchval("select to_regclass('pg_temp.quota_objects') is null")
    finally:
        # Also rolls back any failed fixture assertion, leaving no persistent DDL.
        await connection.close()
