"""Rollback-only PostgreSQL fixture for identity guards and friendship policies.

The SQL rewrites every application/auth relation and helper to this connection's temporary schema. It never inserts,
updates or deletes a real account. Root QA can execute identity_security_fixture_sql() through Supabase execute_sql;
pytest only connects when an explicit loopback-only IDENTITY_SQL_FIXTURE_URL is supplied.
"""

import os
from pathlib import Path
from urllib.parse import urlsplit

import asyncpg
import pytest

MIGRATION = Path(__file__).resolve().parents[2] / "supabase/migrations/20261104073217_permanent_identity_and_friendships.sql"


def identity_security_fixture_sql():
    migration = MIGRATION.read_text(encoding="utf-8")
    migration = "\n".join(line for line in migration.splitlines()
                          if not line.startswith("create schema if not exists jobrun_private")
                          and not line.startswith("revoke all on schema jobrun_private"))
    for original, temporary in (("public.user_profile", "pg_temp.fixture_user_profile"),
                                 ("auth.users", "pg_temp.fixture_auth_users"),
                                 ("public.friendship", "pg_temp.fixture_friendship"),
                                 ("jobrun_private.", "pg_temp.")):
        migration = migration.replace(original, temporary)
    setup = r"""
begin;
set local statement_timeout = '25s';
create temp table fixture_auth_users(id uuid primary key, email text, raw_user_meta_data jsonb default '{}');
create temp table fixture_user_profile(id uuid primary key references pg_temp.fixture_auth_users(id) on delete cascade,
  display_name text, deleted_at timestamptz, updated_at timestamptz default now());
insert into pg_temp.fixture_auth_users(id,email) values
 ('10000000-0000-4000-8000-000000000001','legacy@example.test'),
 ('10000000-0000-4000-8000-000000000002','missing-profile@example.test');
insert into pg_temp.fixture_user_profile(id,display_name) values
 ('10000000-0000-4000-8000-000000000001','Preserved original full name');
create function pg_temp.fixture_handle_new_user() returns trigger language plpgsql security definer set search_path='' as $$
begin
  insert into pg_temp.fixture_user_profile(id,display_name) values(new.id,new.raw_user_meta_data->>'full_name')
  on conflict(id) do nothing;
  return new;
end;
$$;
create trigger on_auth_user_created after insert on pg_temp.fixture_auth_users
for each row execute function pg_temp.fixture_handle_new_user();
alter table pg_temp.fixture_user_profile enable row level security;
grant select on pg_temp.fixture_user_profile to authenticated;
grant update(display_name) on pg_temp.fixture_user_profile to authenticated;
create policy "fixture own profile" on pg_temp.fixture_user_profile for select to authenticated using(id=(select auth.uid()));
create policy "fixture own profile update" on pg_temp.fixture_user_profile for update to authenticated
using(id=(select auth.uid())) with check(id=(select auth.uid()));
"""
    checks = r"""
do $$
declare item text; did_reject boolean; code text;
begin
  if (select count(*) from pg_temp.fixture_user_profile) <> 2 then raise exception 'missing profile not backfilled'; end if;
  if (select count(distinct friend_code) from pg_temp.fixture_user_profile) <> 2 or
     exists(select 1 from pg_temp.fixture_user_profile where friend_code !~ '^[0-9A-F]{8}$') then
    raise exception 'backfill code format or uniqueness failed';
  end if;
  if (select display_name from pg_temp.fixture_user_profile where id='10000000-0000-4000-8000-000000000001')
       <> 'Preserved original full name' then raise exception 'existing profile changed'; end if;
  foreach item in array array['f_u_c_k','f4gg0t','n1gg3r','naz1','kkk','k_k_k','kkkk','fuuuck','fuck123','123fuck',
                             'Ｆｕｃｋ','בן_זונה','שרמוטה','מזדיין','fuckHarel','motherfucker42x','בןזונהHarel','f4gg0tFan'] loop
    if pg_temp.username_reason(item) is distinct from 'offensive' then raise exception 'offensive name accepted: %',item; end if;
  end loop;
  foreach item in array array['Scunthorpe','assistant','classroom','analyst','Dickinson','Cockburn','passion',
                             'Harel_123','שקד_בוזי','as1','FPGA_student','ＦＰＧＡ'] loop
    if pg_temp.username_reason(item) is not null then raise exception 'ordinary name rejected: %',item; end if;
  end loop;
  insert into pg_temp.fixture_auth_users(id,email,raw_user_meta_data) values
    ('10000000-0000-4000-8000-000000000003','alice@example.test','{"username":"Alice","full_name":"Alice Full Name"}'),
    ('10000000-0000-4000-8000-000000000004','bob@example.test','{"username":"Bob"}');
  if (select username from pg_temp.fixture_user_profile where id='10000000-0000-4000-8000-000000000003') <> 'Alice'
     or (select display_name from pg_temp.fixture_user_profile where id='10000000-0000-4000-8000-000000000003') <> 'Alice Full Name'
  then raise exception 'signup identity or full name not preserved'; end if;
  did_reject := false;
  begin insert into pg_temp.fixture_auth_users(id,raw_user_meta_data) values(gen_random_uuid(),'{"username":"alice"}');
  exception when unique_violation then did_reject:=true; end;
  if not did_reject then raise exception 'case-insensitive duplicate accepted'; end if;
  did_reject := false;
  begin insert into pg_temp.fixture_auth_users(id,raw_user_meta_data) values(gen_random_uuid(),'{}');
  exception when check_violation then did_reject:=true; end;
  if not did_reject then raise exception 'signup without username accepted'; end if;
  did_reject := false;
  begin insert into pg_temp.fixture_auth_users(id,raw_user_meta_data) values(gen_random_uuid(),'{"username":"fuckHarel"}');
  exception when check_violation then did_reject:=true; end;
  if not did_reject then raise exception 'signup with offensive username accepted'; end if;
  update pg_temp.fixture_user_profile set username='Harel' where id='10000000-0000-4000-8000-000000000001';
  did_reject := false;
  begin update pg_temp.fixture_user_profile set username='Changed' where id='10000000-0000-4000-8000-000000000001';
  exception when check_violation then did_reject:=true; end;
  if not did_reject then raise exception 'profile username renamed'; end if;
  did_reject := false;
  begin update pg_temp.fixture_user_profile set friend_code='ABCDEF01' where id='10000000-0000-4000-8000-000000000001';
  exception when check_violation then did_reject:=true; end;
  if not did_reject then raise exception 'friend code changed'; end if;
  did_reject := false;
  begin update pg_temp.fixture_auth_users set raw_user_meta_data='{"username":"Changed"}'
        where id='10000000-0000-4000-8000-000000000003';
  exception when check_violation then did_reject:=true; end;
  if not did_reject then raise exception 'auth metadata renamed claimed account'; end if;
  update pg_temp.fixture_auth_users set raw_user_meta_data=raw_user_meta_data||'{"full_name":"Updated full name"}'::jsonb
    where id='10000000-0000-4000-8000-000000000003';
end;
$$;
create temp table fixture_code_candidates(position integer primary key, value text);
insert into pg_temp.fixture_code_candidates values(1,(select friend_code from pg_temp.fixture_user_profile limit 1));
insert into pg_temp.fixture_code_candidates
select 2,upper(substr(md5('free-code-'||n::text),1,8)) from generate_series(1,20) n
where not exists(select 1 from pg_temp.fixture_user_profile p where p.friend_code=upper(substr(md5('free-code-'||n::text),1,8))) limit 1;
create or replace function pg_temp.identity_code_candidate() returns text language plpgsql volatile set search_path='' as $$
declare candidate text;
begin
  delete from pg_temp.fixture_code_candidates where position=(select min(position) from pg_temp.fixture_code_candidates)
    returning value into candidate;
  return coalesce(candidate,upper(substr(replace(pg_catalog.gen_random_uuid()::text,'-',''),1,8)));
end;
$$;
do $$ declare code text; expected text; begin
  select value into expected from pg_temp.fixture_code_candidates where position=2;
  code := pg_temp.allocate_friend_code();
  if code is distinct from expected or exists(select 1 from pg_temp.fixture_code_candidates) then
    raise exception 'random code collision did not retry';
  end if;
end; $$;
insert into pg_temp.fixture_friendship(id,requester_id,recipient_id) values
 ('20000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000003','10000000-0000-4000-8000-000000000001'),
 ('20000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000004');
do $$ declare did_reject boolean:=false; begin
  begin insert into pg_temp.fixture_friendship(requester_id,recipient_id)
  values('10000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000003');
  exception when unique_violation then did_reject:=true; end;
  if not did_reject then raise exception 'reversed duplicate friendship accepted'; end if;
end; $$;
do $$ begin
  execute format('grant usage on schema %I to authenticated, anon', pg_my_temp_schema()::regnamespace);
end; $$;
select set_config('request.jwt.claims','{"sub":"10000000-0000-4000-8000-000000000003","role":"authenticated"}',true);
set local role authenticated;
do $$ declare did_reject boolean; begin
  if (select count(*) from pg_temp.fixture_friendship) <> 1 then raise exception 'friendship participant RLS leaked'; end if;
  if (select count(*) from pg_temp.fixture_user_profile) <> 1 then raise exception 'profile RLS leaked'; end if;
  did_reject := false;
  begin update pg_temp.fixture_user_profile set username='Changed' where id='10000000-0000-4000-8000-000000000003';
  exception when insufficient_privilege then did_reject:=true; end;
  if not did_reject then raise exception 'browser may write username'; end if;
  did_reject := false;
  begin delete from pg_temp.fixture_friendship;
  exception when insufficient_privilege then did_reject:=true; end;
  if not did_reject then raise exception 'browser may mutate friendship'; end if;
  did_reject := false;
  begin perform pg_temp.allocate_friend_code();
  exception when insufficient_privilege then did_reject:=true; end;
  if not did_reject then raise exception 'private allocator exposed'; end if;
end; $$;
reset role;
set local role anon;
do $$ declare did_reject boolean:=false; begin
  begin perform 1 from pg_temp.fixture_friendship;
  exception when insufficient_privilege then did_reject:=true; end;
  if not did_reject then raise exception 'anonymous friendship read permitted'; end if;
end; $$;
reset role;
rollback;
select 'passed' as identity_friendship_fixture, to_regclass('pg_temp.fixture_user_profile') is null as rolled_back;
"""
    return setup + migration + checks


def identity_live_rollback_sql():
    """DML-only post-migration verification using two synthetic accounts, always rolled back.

    This version requires no temporary objects, schema changes or helper replacements. The allocator's forced
    collision branch and legacy-null claim are covered by the isolated fixture/memory tests instead.
    """
    return r"""
begin;
set local statement_timeout='25s';
do $$
declare
  a uuid := gen_random_uuid(); b uuid := gen_random_uuid();
  suffix text := substr(replace(gen_random_uuid()::text,'-',''),1,12);
  name_a text; name_b text; row_a public.user_profile%rowtype; row_b public.user_profile%rowtype;
  item text; did_reject boolean;
begin
  name_a := 'QaA_' || suffix; name_b := 'QaB_' || suffix;
  insert into auth.users(id,aud,role,email,encrypted_password,email_confirmed_at,raw_app_meta_data,raw_user_meta_data,created_at,updated_at)
  values
    (a,'authenticated','authenticated','identity-a-'||suffix||'@example.invalid','',now(),'{"provider":"email","providers":["email"]}',
      jsonb_build_object('username',name_a,'full_name','Synthetic full name A'),now(),now()),
    (b,'authenticated','authenticated','identity-b-'||suffix||'@example.invalid','',now(),'{"provider":"email","providers":["email"]}',
      jsonb_build_object('username',name_b,'full_name','Synthetic full name B'),now(),now());
  select * into strict row_a from public.user_profile where id=a;
  select * into strict row_b from public.user_profile where id=b;
  if row_a.username<>name_a or row_b.username<>name_b or row_a.display_name<>'Synthetic full name A'
     or row_a.friend_code !~ '^[0-9A-F]{8}$' or row_b.friend_code !~ '^[0-9A-F]{8}$' or row_a.friend_code=row_b.friend_code
  then raise exception 'synthetic signup/profile identity mismatch'; end if;
  foreach item in array array['f_u_c_k','f4gg0t','n1gg3r','naz1','kkk','k_k_k','kkkk','fuuuck','fuck123','123fuck',
                             'Ｆｕｃｋ','בן_זונה','שרמוטה','מזדיין','fuckHarel','motherfucker42x','בןזונהHarel','f4gg0tFan'] loop
    if jobrun_private.username_reason(item) is distinct from 'offensive' then raise exception 'offensive name accepted: %',item; end if;
  end loop;
  foreach item in array array['Scunthorpe','assistant','classroom','analyst','Dickinson','Cockburn','passion',
                             'Harel_123','שקד_בוזי','as1','FPGA_student','ＦＰＧＡ'] loop
    if jobrun_private.username_reason(item) is not null then raise exception 'ordinary name rejected: %',item; end if;
  end loop;
  did_reject:=false;
  begin
    insert into auth.users(id,aud,role,email,raw_user_meta_data)
    values(gen_random_uuid(),'authenticated','authenticated','identity-duplicate-'||suffix||'@example.invalid',
           jsonb_build_object('username',lower(name_a)));
  exception when unique_violation then did_reject:=true; end;
  if not did_reject then raise exception 'duplicate normalized signup accepted'; end if;
  did_reject:=false;
  begin insert into auth.users(id,aud,role,email,raw_user_meta_data)
    values(gen_random_uuid(),'authenticated','authenticated','identity-missing-'||suffix||'@example.invalid','{}');
  exception when check_violation then did_reject:=true; end;
  if not did_reject then raise exception 'signup without username accepted'; end if;
  did_reject:=false;
  begin insert into auth.users(id,aud,role,email,raw_user_meta_data)
    values(gen_random_uuid(),'authenticated','authenticated','identity-offensive-'||suffix||'@example.invalid','{"username":"fuckHarel"}');
  exception when check_violation then did_reject:=true; end;
  if not did_reject then raise exception 'offensive signup accepted'; end if;
  did_reject:=false;
  begin update public.user_profile set username='Changed_'||suffix where id=a;
  exception when check_violation then did_reject:=true; end;
  if not did_reject then raise exception 'claimed profile username changed'; end if;
  did_reject:=false;
  begin update public.user_profile set friend_code=row_b.friend_code where id=a;
  exception when check_violation then did_reject:=true; end;
  if not did_reject then raise exception 'friend code changed'; end if;
  did_reject:=false;
  begin update auth.users set raw_user_meta_data=jsonb_build_object('username','Changed_'||suffix) where id=a;
  exception when check_violation then did_reject:=true; end;
  if not did_reject then raise exception 'auth metadata changed username'; end if;
  update auth.users set raw_user_meta_data=raw_user_meta_data||'{"full_name":"Updated synthetic full name"}'::jsonb where id=a;
  update public.user_profile set display_name='Updated synthetic display name' where id=a;
  if (select friend_code from public.user_profile where id=a)<>row_a.friend_code then raise exception 'code was not stable'; end if;
  insert into public.friendship(requester_id,recipient_id) values(a,b);
  did_reject:=false;
  begin insert into public.friendship(requester_id,recipient_id) values(b,a);
  exception when unique_violation then did_reject:=true; end;
  if not did_reject then raise exception 'reversed duplicate friendship accepted'; end if;
  did_reject:=false;
  begin insert into public.friendship(requester_id,recipient_id) values(a,a);
  exception when check_violation then did_reject:=true; end;
  if not did_reject then raise exception 'self friendship accepted'; end if;
  if has_column_privilege('authenticated','public.user_profile','username','UPDATE')
    or has_column_privilege('authenticated','public.user_profile','friend_code','UPDATE')
    or has_table_privilege('authenticated','public.friendship','INSERT,UPDATE,DELETE')
    or has_table_privilege('anon','public.friendship','SELECT')
    or has_function_privilege('authenticated','jobrun_private.allocate_friend_code()','EXECUTE')
  then raise exception 'browser identity/friendship/private function privileges too broad'; end if;
  perform set_config('jobrun.identity_fixture_user',a::text,true);
end;
$$;
select set_config('request.jwt.claims',jsonb_build_object('sub',current_setting('jobrun.identity_fixture_user'),
                                                       'role','authenticated')::text,true);
set local role authenticated;
do $$ declare did_reject boolean; begin
  if (select count(*) from public.friendship)<>1 then raise exception 'friendship participant RLS mismatch'; end if;
  if (select count(*) from public.user_profile)<>1 then raise exception 'profile own-row RLS mismatch'; end if;
  did_reject:=false;
  begin delete from public.friendship;
  exception when insufficient_privilege then did_reject:=true; end;
  if not did_reject then raise exception 'browser can mutate friendships'; end if;
end; $$;
reset role;
rollback;
select 'passed' as synthetic_identity_friendship_rollback;
"""


@pytest.mark.skipif(not os.environ.get("IDENTITY_SQL_FIXTURE_URL"), reason="explicit local SQL fixture URL not set")
async def test_postgres_identity_guards_and_friendship_rls_in_temporary_tables():
    url = os.environ["IDENTITY_SQL_FIXTURE_URL"].replace("postgresql+asyncpg://", "postgresql://", 1)
    assert urlsplit(url).hostname in {"localhost", "127.0.0.1", "::1"}, "pytest identity SQL fixture is local only"
    connection = await asyncpg.connect(url, timeout=10)
    try:
        await connection.execute(identity_security_fixture_sql())
        assert await connection.fetchval("select to_regclass('pg_temp.fixture_user_profile') is null")
    finally:
        await connection.close()
