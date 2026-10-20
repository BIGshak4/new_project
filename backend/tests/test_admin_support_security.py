"""Founder/support SQL behavior on isolated, rollback-only synthetic tables.

The production migration is compiled and exercised, with schema-qualified names
redirected into this connection's pg_temp namespace. No real Auth user, bank,
report, profile, bucket or Storage object is read or modified. The same generated
SQL can be executed via Supabase MCP when a direct connection is unavailable.
"""

from __future__ import annotations

import re
from pathlib import Path

import asyncpg
import pytest

from app.config import get_settings


MIGRATION = Path(__file__).resolve().parents[2] / "supabase/migrations/20261020191024_founder_admin_and_support.sql"
CONFLICT_MIGRATION = MIGRATION.with_name("20261020192330_admin_conflict_http_status.sql")


def admin_support_fixture_sql() -> str:
    source = MIGRATION.read_text(encoding="utf-8") + "\n" + CONFLICT_MIGRATION.read_text(encoding="utf-8")
    # Private implementation names and parsed public wrappers remain separate.
    source = source.replace("create function public.jr_", "create function pg_temp.rpc_jr_")
    source = source.replace("function public.'||signature", "function pg_temp.rpc_'||signature")
    source = source.replace("function jobrun_private.'||signature", "function pg_temp.'||signature")
    source = source.replace("jobrun_private.", "pg_temp.")
    source = source.replace("auth.uid()", "pg_temp.fixture_uid()")
    source = source.replace("auth.users", "pg_temp.fixture_auth_users")
    source = source.replace("storage.objects", "pg_temp.fixture_storage_objects")
    source = source.replace("storage.buckets", "pg_temp.fixture_storage_buckets")
    source = source.replace("public.", "pg_temp.fixture_")
    # The migration has no data modifications outside its new bucket and tables.
    setup = r"""
begin;
set local statement_timeout='30s';
set local lock_timeout='2s';
create function pg_temp.fixture_uid() returns uuid language sql stable as $$
  select (nullif(current_setting('request.jwt.claims',true),'')::jsonb->>'sub')::uuid
$$;
create type pg_temp.fixture_plan_tier as enum('free','pro','team');
create table pg_temp.fixture_auth_users(id uuid primary key,email text,email_confirmed_at timestamptz,
  created_at timestamptz default now(),last_sign_in_at timestamptz,deleted_at timestamptz);
create table pg_temp.fixture_user_profile(id uuid primary key references pg_temp.fixture_auth_users(id) on delete cascade,
  display_name text,plan_tier pg_temp.fixture_plan_tier default 'free');
create table pg_temp.fixture_jr_members(email text primary key,display_name text,can_manage_tasks boolean default false);
create table pg_temp.fixture_question(id uuid primary key,key text,assets jsonb);
create table pg_temp.fixture_question_report(id uuid primary key,question_id uuid references pg_temp.fixture_question(id),
  user_id uuid references pg_temp.fixture_auth_users(id),reason text,note text,language text,context text,
  created_at timestamptz default now(),resolved_at timestamptz,resolved_by text);
create table pg_temp.fixture_storage_objects(id uuid primary key default gen_random_uuid(),bucket_id text,name text,metadata jsonb,unique(bucket_id,name));
alter table pg_temp.fixture_storage_objects enable row level security;
grant select,insert,update,delete on pg_temp.fixture_storage_objects to authenticated;
create table pg_temp.fixture_storage_buckets(id text primary key,name text,public boolean,file_size_limit bigint,allowed_mime_types text[]);
create table pg_temp.fixture_results(name text primary key);
grant select,insert on pg_temp.fixture_results to authenticated;
create function pg_temp.check_true(condition boolean, label text) returns void language plpgsql security invoker as $$
begin
  if condition is distinct from true then raise exception 'Assertion failed: %',label; end if;
  insert into pg_temp.fixture_results values(label);
end $$;
create function pg_temp.expect_error(statement text,expected_code text,label text) returns void language plpgsql security invoker as $$
declare caught text;
begin
  begin execute statement;
  exception when others then get stacked diagnostics caught=returned_sqlstate;
    if caught<>expected_code then raise exception 'Wrong SQLSTATE for %: %',label,caught; end if;
    insert into pg_temp.fixture_results values(label); return;
  end;
  raise exception 'Expected rejection: %',label;
end $$;
""" + source
    cases = r"""

insert into pg_temp.fixture_auth_users(id,email,email_confirmed_at) values
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','founder@example.invalid',now()),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','learner@example.invalid',now()),
  ('cccccccc-cccc-cccc-cccc-cccccccccccc','outsider@example.invalid',now()),
  ('dddddddd-dddd-dddd-dddd-dddddddddddd','unconfirmed@example.invalid',null);
insert into pg_temp.fixture_user_profile(id,display_name) values
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','Founder'),('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','Learner');
insert into pg_temp.fixture_jr_members values('founder@example.invalid','Founder',true),('learner@example.invalid','Learner',false);
insert into pg_temp.fixture_question values('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee','example-unit','{"titles":{"he":"דוגמה","en":"Example"}}');
insert into pg_temp.fixture_question_report values('ffffffff-ffff-ffff-ffff-ffffffffffff','eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
  'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','unclear','A note','he','practice',now(),null,null);

-- Authentication and forged metadata cannot confer founder authority.
select set_config('request.jwt.claims','{}',true);
select pg_temp.expect_error('select pg_temp.rpc_jr_admin_users()','42501','anonymous directory denied');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_submit_support_report(gen_random_uuid(),'subject','description','bug','he','/',null)$q$,
  '42501','anonymous report denied');
select set_config('request.jwt.claims','{"sub":"dddddddd-dddd-dddd-dddd-dddddddddddd"}',true);
select pg_temp.expect_error('select pg_temp.rpc_jr_admin_users()','42501','unconfirmed account denied');
select set_config('request.jwt.claims','{"sub":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb","user_metadata":{"can_manage_tasks":true}}',true);
select pg_temp.expect_error('select pg_temp.rpc_jr_admin_users()','42501','forged metadata founder denied');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_update_user('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','pro',true,'free',true)$q$,
  '42501','self plan escalation denied');
select set_config('request.jwt.claims','{"sub":"cccccccc-cccc-cccc-cccc-cccccccccccc"}',true);
select pg_temp.expect_error('select pg_temp.rpc_jr_admin_users()','42501','outsider directory denied');

select set_config('request.jwt.claims','{"sub":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}',true);
select pg_temp.check_true((pg_temp.rpc_jr_admin_users('LEARNER',1,25)->>'total')::int=1,'case insensitive user search');
select pg_temp.check_true((pg_temp.rpc_jr_admin_users('outsider',1,25)->'users'->0->>'plan_tier')='free','missing profile safe default');
select pg_temp.check_true((pg_temp.rpc_jr_admin_update_user('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','pro',true,'free',true)->>'plan_tier')='pro','founder can assign manual plan');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_update_user('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','team',true,'free',true)$q$,
  'PT409','stale plan update rejected');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_update_user('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','free',false,'free',true)$q$,
  '42501','founder removal protected');
select pg_temp.check_true((select count(*)=1 from pg_temp.fixture_jr_admin_events where action='user_updated'),'plan audit server generated');
select pg_temp.check_true((pg_temp.rpc_jr_admin_question_reports()->'reports'->0->>'question_title_he')='דוגמה','legacy question queue includes localized title');
select pg_temp.check_true((pg_temp.rpc_jr_admin_resolve_question_report('ffffffff-ffff-ffff-ffff-ffffffffffff',true)->>'resolved_at') is not null,'legacy report resolves');

-- Confirmed, non-pilot accounts may report an access problem; no admin grant.
select set_config('request.jwt.claims','{"sub":"cccccccc-cccc-cccc-cccc-cccccccccccc"}',true);
select pg_temp.check_true((pg_temp.rpc_jr_submit_support_report('10000000-0000-0000-0000-000000000001','Access','Cannot enter','other','en','/',null)->>'id') is not null,
  'confirmed outsider may report access issue');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_submit_support_report(gen_random_uuid(),'subject','description','bug','he','//evil.invalid',null)$q$,
  '22023','external page locator rejected');

select set_config('request.jwt.claims','{"sub":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}',true);
select pg_temp.check_true(not(pg_temp.rpc_jr_submit_support_report('10000000-0000-0000-0000-000000000002','Broken brackets','Y[3:0] details','bug','he','/questions','example-unit') ? 'internal_notes'),
  'submit receipt hides internal notes');
select pg_temp.check_true((pg_temp.rpc_jr_submit_support_report('10000000-0000-0000-0000-000000000002','Retry','Details','bug','he','/',null)->>'subject')='Broken brackets','idempotent report creation');
select pg_temp.check_true((select count(*)=1 from pg_temp.fixture_jr_support_reports where reporter_id='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'),'retry does not consume rate allowance');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_support_detail('10000000-0000-0000-0000-000000000002')$q$,
  '42501','owner denied private admin detail');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_reserve_support_file(gen_random_uuid(),'10000000-0000-0000-0000-000000000001','a.png','image/png',12)$q$,
  '42501','foreign report reservation denied');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_reserve_support_file(gen_random_uuid(),'10000000-0000-0000-0000-000000000002','a.svg','image/svg+xml',12)$q$,
  '22023','active file type denied');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_reserve_support_file(gen_random_uuid(),'10000000-0000-0000-0000-000000000002','a.pdf','image/png',12)$q$,
  '22023','extension MIME mismatch denied');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_reserve_support_file(gen_random_uuid(),'10000000-0000-0000-0000-000000000002','a.pdf','application/pdf',5242881)$q$,
  '22023','per-file byte limit denied');

select pg_temp.rpc_jr_reserve_support_file('20000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000002','sample.png','image/png',12);
select pg_temp.check_true((pg_temp.rpc_jr_reserve_support_file('20000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000002','sample.png','image/png',12)->>'storage_path')=
  'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb/10000000-0000-0000-0000-000000000002/20000000-0000-0000-0000-000000000001.png','idempotent canonical storage reservation');
select pg_temp.check_true((select count(*)=1 from pg_temp.fixture_jr_support_files),'file retry consumes one slot');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_reserve_support_file('20000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000002','sample.png','image/png',99)$q$,
  '22023','reservation size cannot change');
select pg_temp.check_true(pg_temp.jr_can_upload_support_file('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb/10000000-0000-0000-0000-000000000002/20000000-0000-0000-0000-000000000001.png','{"mimetype":"image/png"}'),
  'Storage preflight incomplete size accepted');
select set_config('request.jwt.claims','{}',true);
insert into pg_temp.fixture_storage_objects(bucket_id,name,metadata) values('jr-support-files',
  'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb/10000000-0000-0000-0000-000000000002/20000000-0000-0000-0000-000000000001.png','{"size":12,"mimetype":"image/png"}');
select pg_temp.check_true(true,'internal Storage persistence needs no auth subject');
select pg_temp.expect_error($q$update pg_temp.fixture_storage_objects set metadata='{"size":13,"mimetype":"image/png"}'$q$,
  '23514','committed size mismatch rejected');
select pg_temp.expect_error($q$update pg_temp.fixture_storage_objects set metadata='{"size":12,"mimetype":"text/plain"}'$q$,
  '23514','committed MIME mismatch rejected');
select pg_temp.expect_error($q$update pg_temp.fixture_storage_objects set metadata='{}'$q$,
  '23514','internal persistence cannot omit size');
select pg_temp.expect_error($q$update pg_temp.fixture_storage_objects set name='renamed.png'$q$,
  '23514','storage rename denied');
select pg_temp.expect_error($q$insert into pg_temp.fixture_storage_objects(bucket_id,name,metadata) values('jr-support-files','unreserved.png','{"size":12,"mimetype":"image/png"}')$q$,
  '23514','unreserved storage object denied');

select set_config('request.jwt.claims','{"sub":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}',true);
select pg_temp.check_true(not pg_temp.rpc_jr_remove_support_file('20000000-0000-0000-0000-000000000001'),'completed upload reservation cannot be removed');
select pg_temp.rpc_jr_reserve_support_file('20000000-0000-0000-0000-000000000002','10000000-0000-0000-0000-000000000002','pending.txt','text/plain',5);
select pg_temp.check_true(pg_temp.rpc_jr_remove_support_file('20000000-0000-0000-0000-000000000002'),'failed upload releases reserved slot');
select pg_temp.rpc_jr_reserve_support_file(gen_random_uuid(),'10000000-0000-0000-0000-000000000002','slot.txt','text/plain',1) from generate_series(1,4);
select pg_temp.expect_error($q$select pg_temp.rpc_jr_reserve_support_file(gen_random_uuid(),'10000000-0000-0000-0000-000000000002','sixth.txt','text/plain',1)$q$,
  '23514','sixth file denied');

-- Real browser role tests: grants and RLS are not replaced with mocked booleans.
set local role authenticated;
select pg_temp.check_true((select count(*)=1 from pg_temp.fixture_jr_support_reports),'reporter sees own report only');
select pg_temp.expect_error('select internal_notes from pg_temp.fixture_jr_support_reports','42501','internal notes column unreadable');
select pg_temp.expect_error($q$update pg_temp.fixture_jr_support_reports set status='closed'$q$,'42501','reporter cannot update ticket status');
select pg_temp.expect_error($q$insert into pg_temp.fixture_jr_admin_events(action) values('forged')$q$,'42501','audit forgery denied');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_users()$q$,'42501','invoker wrapper retains founder guard');
select pg_temp.check_true((select count(*)=1 from pg_temp.fixture_storage_objects),'owner storage SELECT authorized');
select pg_temp.expect_error($q$insert into pg_temp.fixture_storage_objects(bucket_id,name,metadata) values('jr-support-files','arbitrary.txt','{"size":1,"mimetype":"text/plain"}')$q$,
  '23514','direct unreserved insert cannot bypass trigger');
select set_config('request.jwt.claims','{"sub":"cccccccc-cccc-cccc-cccc-cccccccccccc"}',true);
select pg_temp.check_true((select count(*)=0 from pg_temp.fixture_storage_objects),'foreign storage SELECT hidden');
select pg_temp.check_true((select count(*)=0 from pg_temp.fixture_jr_support_files),'foreign reservation rows hidden');
reset role;

select set_config('request.jwt.claims','{"sub":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}',true);
select pg_temp.check_true((pg_temp.rpc_jr_admin_support_list('10000000-0000-0000-0000-000000000002','open',1,25)->>'total')::int=1,'founder support search by UUID');
select pg_temp.check_true(exists(select 1 from jsonb_array_elements(pg_temp.rpc_jr_admin_support_detail('10000000-0000-0000-0000-000000000002')->'files') f
  where f->>'id'='20000000-0000-0000-0000-000000000001' and (f->>'uploaded')::boolean),'admin identifies actual uploaded object');
select pg_temp.check_true((pg_temp.rpc_jr_admin_update_support('10000000-0000-0000-0000-000000000002',1,'in_progress','high',
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','secret internal note','')->>'version')::int=2,'founder triage increments version');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_update_support('10000000-0000-0000-0000-000000000002',1,'closed','normal',null,'','')$q$,
  'PT409','stale support edit denied');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_update_support('10000000-0000-0000-0000-000000000002',2,'open','normal',
  'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','','')$q$,'22023','learner assignment denied');
select pg_temp.check_true((select count(*)=2 from pg_temp.fixture_jr_admin_events where report_id='10000000-0000-0000-0000-000000000002'),'report creation and triage audited');
select set_config('request.jwt.claims','{"sub":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}',true);
select pg_temp.check_true(not(pg_temp.rpc_jr_submit_support_report('10000000-0000-0000-0000-000000000002','Retry','Details','bug','he','/',null) ? 'internal_notes'),
  'idempotent receipt still hides newly added notes');
select pg_temp.rpc_jr_submit_support_report(gen_random_uuid(),'rate','description','bug','he','/',null) from generate_series(1,4);
select pg_temp.expect_error($q$select pg_temp.rpc_jr_submit_support_report(gen_random_uuid(),'sixth','description','bug','he','/',null)$q$,
  '23514','sixth report in rolling day denied');

-- Independent byte boundaries, not merely frontend file-count validation.
select set_config('request.jwt.claims','{"sub":"cccccccc-cccc-cccc-cccc-cccccccccccc"}',true);
select pg_temp.rpc_jr_submit_support_report('10000000-0000-0000-0000-000000000003','Large file set','description','bug','en','/',null);
select pg_temp.rpc_jr_reserve_support_file(gen_random_uuid(),'10000000-0000-0000-0000-000000000003','large.pdf','application/pdf',5242880)
  from generate_series(1,3);
select pg_temp.check_true((select sum(size_bytes)=15728640 from pg_temp.fixture_jr_support_files where report_id='10000000-0000-0000-0000-000000000003'),
  '15 MiB per report boundary accepted');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_reserve_support_file(gen_random_uuid(),'10000000-0000-0000-0000-000000000003','over.txt','text/plain',1)$q$,
  '23514','per report aggregate bytes rejected before fifth slot');
select pg_temp.check_true(pg_temp.rpc_jr_remove_support_file(gen_random_uuid()),'absent reservation cleanup idempotent');

-- Synthetic historical allocations bring the outsider to exactly 100 MiB.
-- These fixture-only writes do not bypass a real application table policy.
insert into pg_temp.fixture_jr_support_files(id,report_id,owner_id,storage_path,name,mime_type,size_bytes)
  select gen_random_uuid(),'10000000-0000-0000-0000-000000000001','cccccccc-cccc-cccc-cccc-cccccccccccc',
    'historical/'||n||'.pdf','historical.pdf','application/pdf',5242880 from generate_series(1,17) n;
select pg_temp.check_true((select sum(size_bytes)=104857600 from pg_temp.fixture_jr_support_files where owner_id='cccccccc-cccc-cccc-cccc-cccccccccccc'),
  '100 MiB user lifetime boundary accepted');
select pg_temp.rpc_jr_submit_support_report('10000000-0000-0000-0000-000000000004','New empty report','description','bug','en','/',null);
select pg_temp.expect_error($q$select pg_temp.rpc_jr_reserve_support_file(gen_random_uuid(),'10000000-0000-0000-0000-000000000004','over.txt','text/plain',1)$q$,
  '23514','user lifetime quota enforced');

"""
    # A procedural test body keeps assertions and synthetic identities together.
    cases = re.sub(r"^select (?=pg_temp\.|set_config\()", "perform ", cases, flags=re.MULTILINE)
    return setup + "\ndo $qa$ begin\n" + cases + r"""
  if (select count(*) from pg_temp.fixture_results)<40 then raise exception 'Too few security assertions'; end if;
end $qa$;
rollback;
select 'passed' as admin_support_fixture,to_regclass('pg_temp.fixture_auth_users') is null as rolled_back;
"""


def test_admin_support_rpc_surface_has_no_public_definer_or_broad_data_grant():
    source = MIGRATION.read_text(encoding="utf-8")
    assert not re.search(r"create function public\.[^$]+?security definer", source, re.IGNORECASE)
    assert "grant usage on schema jobrun_private" not in source.lower()
    assert "begin atomic" in source.lower()
    assert "grant execute on function jobrun_private." in source.lower()
    assert "or m.can_manage_tasks" not in source  # no blanket profile-read policy
    report_grant = re.search(r"grant select\((.*?)\)\s+on public\.jr_support_reports", source, re.DOTALL)
    assert report_grant and "internal_notes" not in report_grant.group(1)


@pytest.mark.skipif(not get_settings().database_url, reason="DATABASE_URL not configured")
async def test_admin_support_rollback_only_security_behavior():
    url = get_settings().database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    try:
        connection = await asyncpg.connect(url, timeout=20, statement_cache_size=0)
    except (asyncpg.InvalidPasswordError, OSError):
        pytest.skip("Local direct database connection unavailable; run admin_support_fixture_sql through Supabase MCP")
    try:
        await connection.execute(admin_support_fixture_sql())
        assert await connection.fetchval("select to_regclass('pg_temp.fixture_auth_users') is null")
    finally:
        await connection.close()
