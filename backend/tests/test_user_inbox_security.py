"""In-app inbox behavior against isolated temporary SQL fixtures, always rolled back.

Broadcast publication tests never touch actual announcements or recipients. The
full deployed migration bodies are reused, changing only schema-qualified names.
Run user_inbox_fixture_sql() through Supabase MCP if the direct local DB secret
is unavailable. No live users, their reports, or credentials are inspected.
"""

from __future__ import annotations

import re
from pathlib import Path

import asyncpg
import pytest

from app.config import get_settings
from tests.test_admin_support_security import admin_support_fixture_sql

MIGRATION = Path(__file__).resolve().parents[2] / "supabase/migrations/20261020195623_user_updates_and_support_inbox.sql"


def user_inbox_fixture_sql() -> str:
    setup = admin_support_fixture_sql().split("insert into pg_temp.fixture_auth_users(id,email,email_confirmed_at)", 1)[0].rsplit("do $qa$ begin", 1)[0]
    source = MIGRATION.read_text(encoding="utf-8")
    source = source.replace("create function public.jr_", "create function pg_temp.rpc_jr_")
    source = source.replace("function public.'||signature", "function pg_temp.rpc_'||signature")
    source = source.replace("function jobrun_private.'||signature", "function pg_temp.'||signature")
    source = source.replace("jobrun_private.", "pg_temp.")
    source = source.replace("auth.uid()", "pg_temp.fixture_uid()")
    source = source.replace("auth.users", "pg_temp.fixture_auth_users")
    source = source.replace("storage.objects", "pg_temp.fixture_storage_objects")
    source = source.replace("public.", "pg_temp.fixture_")
    # A fixture-only receipt trigger injects a fresh personal message during the
    # mark-all statement. Separate INSERT/UPDATE statements would mark it read;
    # a single data-modifying CTE snapshot correctly leaves the arrival unread.
    arrival_trigger = r"""
create function pg_temp.inject_unread_during_mark_all() returns trigger language plpgsql as $$
begin
  if new.user_id='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb' and new.announcement_id='10000000-0000-0000-0000-000000000002' then
    insert into pg_temp.fixture_jr_support_updates(report_id,recipient_id,update_kind,body,language,status,report_version)
      values('20000000-0000-0000-0000-000000000001',new.user_id,'message','New arrival during mark all','en','resolved',99);
  end if;
  return new;
end $$;
create trigger fixture_inbox_arrival after insert on pg_temp.fixture_jr_announcement_reads
  for each row execute function pg_temp.inject_unread_during_mark_all();
"""
    cases = r"""
insert into pg_temp.fixture_auth_users(id,email,email_confirmed_at) values
 ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','founder@example.invalid',now()),
 ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','learner@example.invalid',now()),
 ('cccccccc-cccc-cccc-cccc-cccccccccccc','other@example.invalid',now()),
 ('dddddddd-dddd-dddd-dddd-dddddddddddd','unconfirmed@example.invalid',null);
insert into pg_temp.fixture_user_profile(id,display_name) values
 ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','Founder'),('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','Learner');
insert into pg_temp.fixture_jr_members values('founder@example.invalid','Founder',true),('learner@example.invalid','Learner',false);
select set_config('request.jwt.claims','{}',true);
select pg_temp.expect_error('select pg_temp.rpc_jr_user_inbox()','42501','anonymous inbox denied');
select pg_temp.expect_error('select pg_temp.rpc_jr_mark_all_inbox_read()','42501','anonymous read write denied');
select set_config('request.jwt.claims','{"sub":"dddddddd-dddd-dddd-dddd-dddddddddddd"}',true);
select pg_temp.expect_error('select pg_temp.rpc_jr_user_inbox()','42501','unconfirmed inbox denied');
select set_config('request.jwt.claims','{"sub":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb","user_metadata":{"can_manage_tasks":true}}',true);
select pg_temp.expect_error('select pg_temp.rpc_jr_admin_announcements()','42501','forged metadata cannot manage broadcasts');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_save_announcement(gen_random_uuid(),0,'title','body')$q$,'42501','learner cannot create broadcast');
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox()->>'total')::int=0,'new inbox empty');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_user_inbox('all',0,25,'he')$q$,'22023','invalid pagination rejected');

-- Drafts never become visible, and publishing creates no per-account fanout.
select set_config('request.jwt.claims','{"sub":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}',true);
select pg_temp.check_true((pg_temp.rpc_jr_admin_save_announcement('10000000-0000-0000-0000-000000000001',0,'עדכון','תוכן בעברית')->>'version')::int=1,'draft version starts at one');
select pg_temp.check_true((pg_temp.rpc_jr_admin_announcements('10000000-0000-0000-0000-000000000001')->>'total')::int=1,'admin searches announcement recovery UUID');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_save_announcement(gen_random_uuid(),0,'כותרת','תוכן','English title',null)$q$,'22023','partial English pair rejected');
select set_config('request.jwt.claims','{"sub":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}',true);
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox()->>'total')::int=0,'draft hidden from recipient');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_mark_inbox_read('announcement','10000000-0000-0000-0000-000000000001')$q$,'42501','draft cannot acquire read receipt');
select set_config('request.jwt.claims','{"sub":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}',true);
select pg_temp.check_true((pg_temp.rpc_jr_admin_save_announcement('10000000-0000-0000-0000-000000000001',1,'עדכון','תוכן בעברית',null,null,'publish')->>'status')='published','founder publishes saved draft');
select pg_temp.rpc_jr_admin_save_announcement('10000000-0000-0000-0000-000000000002',0,'כותרת שנייה','תוכן שני','Second update','English body','publish');
select pg_temp.check_true((select count(*)=2 from pg_temp.fixture_jr_announcements),'broadcast stored once for all users');
select pg_temp.check_true((select count(*)=0 from pg_temp.fixture_jr_announcement_reads),'publishing does not fan out read rows');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_save_announcement('10000000-0000-0000-0000-000000000001',1,'שינוי','תוכן')$q$,'PT409','stale broadcast edit rejected');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_save_announcement('10000000-0000-0000-0000-000000000001',2,'שינוי','תוכן')$q$,'22023','published broadcast cannot be edited');
select pg_temp.expect_error($q$update pg_temp.fixture_jr_announcements set body_he='mutation' where id='10000000-0000-0000-0000-000000000001'$q$,'22023','published immutability enforced by trigger');

select set_config('request.jwt.claims','{"sub":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}',true);
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox('all',1,25,'en')->>'unread_count')::int=2,'published broadcasts initially unread');
select pg_temp.check_true(exists(select 1 from jsonb_array_elements(pg_temp.rpc_jr_user_inbox('all',1,25,'en')->'items') i where i->>'id'='10000000-0000-0000-0000-000000000001' and i->>'language'='he' and i->>'body'='תוכן בעברית'),'English request explicitly reports Hebrew fallback');
select pg_temp.check_true(exists(select 1 from jsonb_array_elements(pg_temp.rpc_jr_user_inbox('all',1,25,'en')->'items') i where i->>'id'='10000000-0000-0000-0000-000000000002' and i->>'language'='en' and i->>'body'='English body'),'English pair displayed when supplied');
select pg_temp.check_true(jsonb_array_length(pg_temp.rpc_jr_user_inbox('all',1,1,'he')->'items')=1,'inbox page bounded');
select pg_temp.rpc_jr_mark_inbox_read('announcement','10000000-0000-0000-0000-000000000001');
select pg_temp.rpc_jr_mark_inbox_read('announcement','10000000-0000-0000-0000-000000000001');
select pg_temp.check_true((select count(*)=1 from pg_temp.fixture_jr_announcement_reads),'read receipt retries idempotent');
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox()->>'unread_count')::int=1,'read receipt decrements own badge');
select set_config('request.jwt.claims','{"sub":"cccccccc-cccc-cccc-cccc-cccccccccccc"}',true);
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox()->>'unread_count')::int=2,'another account read state independent');

-- Original receipt, private workflow, public status and idempotent public reply.
select set_config('request.jwt.claims','{"sub":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}',true);
select pg_temp.check_true(not(pg_temp.rpc_jr_submit_support_report('20000000-0000-0000-0000-000000000001','פנייה','הבעיה שלי','bug','he','/',null) ?| array['internal_notes','assigned_to','reporter_id']), 'submission hides internal identities and notes');
select pg_temp.rpc_jr_submit_support_report('20000000-0000-0000-0000-000000000001','retry','retry','bug','he','/',null);
select pg_temp.check_true((select count(*)=1 from pg_temp.fixture_jr_support_updates),'one received update despite submission retry');
select pg_temp.check_true((pg_temp.rpc_jr_my_support_reports()->>'total')::int=1,'owner support history persisted');
select pg_temp.check_true(jsonb_array_length(pg_temp.rpc_jr_my_support_detail('20000000-0000-0000-0000-000000000001')->'updates')=1,'owner sees original received timeline');
select set_config('request.jwt.claims','{"sub":"cccccccc-cccc-cccc-cccc-cccccccccccc"}',true);
select pg_temp.check_true((pg_temp.rpc_jr_my_support_reports()->>'total')::int=0,'foreign support history absent');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_my_support_detail('20000000-0000-0000-0000-000000000001')$q$,'42501','foreign detail blocked');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_reply_support('20000000-0000-0000-0000-000000000001',1,gen_random_uuid(),'forged')$q$,'42501','nonfounder reply blocked');

select set_config('request.jwt.claims','{"sub":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}',true);
select pg_temp.rpc_jr_admin_update_support('20000000-0000-0000-0000-000000000001',1,'open','high','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','PRIVATE_SECRET_NOTE','');
select pg_temp.check_true((select count(*)=1 from pg_temp.fixture_jr_support_updates),'private triage edits do not notify user');
select pg_temp.rpc_jr_admin_update_support('20000000-0000-0000-0000-000000000001',2,'in_progress','high','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','PRIVATE_SECRET_NOTE','');
select pg_temp.check_true((select count(*)=2 from pg_temp.fixture_jr_support_updates),'public status change notifies once');
select pg_temp.check_true((pg_temp.rpc_jr_admin_reply_support('20000000-0000-0000-0000-000000000001',3,'30000000-0000-0000-0000-000000000001','אנחנו בודקים את הבעיה',null,'he')->'report'->>'version')::int=4,'public reply increments shared report version');
select pg_temp.rpc_jr_admin_reply_support('20000000-0000-0000-0000-000000000001',3,'30000000-0000-0000-0000-000000000001','אנחנו בודקים את הבעיה',null,'he');
select pg_temp.check_true((select count(*)=3 from pg_temp.fixture_jr_support_updates),'public reply ambiguous retry creates no duplicate');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_reply_support('20000000-0000-0000-0000-000000000001',3,'30000000-0000-0000-0000-000000000001','different payload',null,'he')$q$,'PT409','changed idempotency payload rejected');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_reply_support('20000000-0000-0000-0000-000000000001',3,gen_random_uuid(),'stale message',null,'he')$q$,'PT409','stale new reply rejected');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_update_support('20000000-0000-0000-0000-000000000001',4,'resolved','normal',null,'','  ')$q$,'22023','closing requires public resolution');
select pg_temp.check_true((select count(*)=3 from pg_temp.fixture_jr_support_updates),'failed close creates no update');
select pg_temp.rpc_jr_admin_update_support('20000000-0000-0000-0000-000000000001',4,'resolved','normal',null,'PRIVATE_SECRET_NOTE','תיקנו את הבעיה');
select pg_temp.check_true((select count(*)=4 from pg_temp.fixture_jr_support_updates),'resolved status publishes public resolution');
select pg_temp.check_true(jsonb_array_length(pg_temp.rpc_jr_admin_support_detail('20000000-0000-0000-0000-000000000001')->'updates')=4,'admin detail includes separate public timeline');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_admin_update_support('20000000-0000-0000-0000-000000000001',5,'resolved','normal',null,'private edit','')$q$,'22023','terminal same-status edit cannot erase public explanation');
select pg_temp.rpc_jr_admin_update_support('20000000-0000-0000-0000-000000000001',5,'resolved','high',null,'private edit','תיקנו את הבעיה');
select pg_temp.check_true((select count(*)=4 from pg_temp.fixture_jr_support_updates),'terminal private edit keeps resolution and creates no notification');

select set_config('request.jwt.claims','{"sub":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}',true);
select pg_temp.check_true(strpos(pg_temp.rpc_jr_my_support_detail('20000000-0000-0000-0000-000000000001')::text,'PRIVATE_SECRET_NOTE')=0,'owner detail never leaks private notes');
select pg_temp.check_true(strpos(pg_temp.rpc_jr_my_support_detail('20000000-0000-0000-0000-000000000001')::text,'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')=0,'owner detail never leaks admin identity');
select pg_temp.check_true(not(pg_temp.rpc_jr_my_support_detail('20000000-0000-0000-0000-000000000001') ? 'events'),'owner detail has no audit trail');
select pg_temp.check_true(exists(select 1 from jsonb_array_elements(pg_temp.rpc_jr_my_support_detail('20000000-0000-0000-0000-000000000001')->'updates') i where i->>'body'='תיקנו את הבעיה' and i->>'status'='resolved'),'owner receives actual public resolution');
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox('support')->>'total')::int=4 and (pg_temp.rpc_jr_user_inbox('support')->>'unread_count')::int=5,'kind filter total with global unread badge');
select pg_temp.rpc_jr_mark_inbox_read('support',(select id from pg_temp.fixture_jr_support_updates where idempotency_id='30000000-0000-0000-0000-000000000001'));
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox()->>'unread_count')::int=4,'personal read state decreases own badge');
select pg_temp.check_true((pg_temp.rpc_jr_mark_all_inbox_read()->>'marked')::int=4,'mark all writes only remaining own unread');
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox()->>'unread_count')::int=1,'arrival during mark all remains unread');
select pg_temp.check_true((pg_temp.rpc_jr_mark_all_inbox_read()->>'marked')::int=1,'later read action acknowledges new arrival');
select pg_temp.check_true((pg_temp.rpc_jr_mark_all_inbox_read()->>'marked')::int=0,'mark all retry idempotent');
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox()->>'unread_count')::int=0,'badge zero after mark all');
select set_config('request.jwt.claims','{"sub":"cccccccc-cccc-cccc-cccc-cccccccccccc"}',true);
select pg_temp.expect_error($q$select pg_temp.rpc_jr_mark_inbox_read('support',(select id from pg_temp.fixture_jr_support_updates limit 1))$q$,'42501','foreign personal read write blocked');
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox('support')->>'total')::int=0,'personal notifications never broadcast');
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox()->>'unread_count')::int=2,'mark all does not read another account broadcasts');

-- Public roles cannot bypass the RPC contract to inject updates, mutate reads,
-- inspect drafts, reveal staff assignments, or fetch private recipients.
set local role authenticated;
select pg_temp.expect_error('select * from pg_temp.fixture_jr_announcements','42501','draft table direct read closed');
select pg_temp.expect_error('select * from pg_temp.fixture_jr_support_updates','42501','raw personal update table direct read closed');
select pg_temp.expect_error('select * from pg_temp.fixture_jr_announcement_reads','42501','raw read receipts direct read closed');
select pg_temp.expect_error($q$insert into pg_temp.fixture_jr_support_updates(report_id,recipient_id,update_kind,body,language,status,report_version)
 values('20000000-0000-0000-0000-000000000001','cccccccc-cccc-cccc-cccc-cccccccccccc','status','forged','en','open',99)$q$,'42501','notification forgery blocked');
select pg_temp.expect_error('select assigned_to from pg_temp.fixture_jr_support_reports','42501','staff identity direct owner column revoked');
select pg_temp.expect_error('select priority from pg_temp.fixture_jr_support_reports','42501','private workflow priority direct owner column revoked');
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox()->>'total')::int=2,'parsed invoker wrapper works with real browser role');
reset role;

select set_config('request.jwt.claims','{"sub":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}',true);
select pg_temp.rpc_jr_admin_save_announcement('10000000-0000-0000-0000-000000000001',2,null,null,null,null,'archive');
select set_config('request.jwt.claims','{"sub":"cccccccc-cccc-cccc-cccc-cccccccccccc"}',true);
select pg_temp.check_true((pg_temp.rpc_jr_user_inbox()->>'total')::int=1 and (pg_temp.rpc_jr_user_inbox()->>'unread_count')::int=1,'archived broadcasts hidden and no longer unread');
select pg_temp.expect_error($q$select pg_temp.rpc_jr_mark_inbox_read('announcement','10000000-0000-0000-0000-000000000001')$q$,'42501','archived broadcast cannot acquire new receipt');
select set_config('request.jwt.claims','{"sub":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}',true);
select pg_temp.rpc_jr_admin_update_support('20000000-0000-0000-0000-000000000001',6,'closed','high',null,'private edit','תיקנו את הבעיה');
select pg_temp.check_true(exists(select 1 from pg_temp.fixture_jr_support_updates where status='closed' and body='תיקנו את הבעיה'),
  'terminal transition notification repeats actual retained explanation');
"""
    cases = re.sub(r"^select (?=pg_temp\.|set_config\()", "perform ", cases, flags=re.MULTILINE)
    return setup + "\n" + source + "\n" + arrival_trigger + "\ndo $qa$ begin\n" + cases + r"""
if (select count(*) from pg_temp.fixture_results)<50 then raise exception 'Too few inbox assertions'; end if;
end $qa$;
rollback;
select 'passed' as user_inbox_fixture,to_regclass('pg_temp.fixture_auth_users') is null as rolled_back;
"""


def test_inbox_surface_preserves_private_schema_and_sparse_broadcast_model():
    source = MIGRATION.read_text(encoding="utf-8")
    assert "grant usage on schema jobrun_private" not in source.lower()
    assert not re.search(r"create function public\.[^$]+?security definer", source, re.IGNORECASE)
    # Publishing never walks users or inserts per-recipient rows.
    publishing = source.split("create function jobrun_private.jr_admin_save_announcement", 1)[1].split("create function jobrun_private.jr_immutable", 1)[0]
    assert "auth.users" not in publishing
    assert "jr_support_updates" not in publishing
    assert "jr_announcement_reads" not in publishing


@pytest.mark.skipif(not get_settings().database_url, reason="DATABASE_URL not configured")
async def test_user_inbox_rollback_security_behavior():
    url = get_settings().database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    try:
        connection = await asyncpg.connect(url, timeout=20, statement_cache_size=0)
    except (asyncpg.InvalidPasswordError, OSError):
        pytest.skip("Local direct database unavailable; same SQL fixture can run via Supabase MCP")
    try:
        await connection.execute(user_inbox_fixture_sql())
        assert await connection.fetchval("select to_regclass('pg_temp.fixture_auth_users') is null")
    finally:
        await connection.close()
