"""Opt-in, read-only checks of deployed database security metadata.

Set SECURITY_DATABASE_CONTRACT_URL explicitly to audit a database. The fixture
starts a READ ONLY transaction; tests inspect catalogs and bucket configuration,
never user rows, credentials, auth records, or application data. These are not
two-user behavioral RLS tests and do not replace those existing integration tests.
"""

from __future__ import annotations

import os

import asyncpg
import pytest
import pytest_asyncio

AUDIT_URL = os.environ.get("SECURITY_DATABASE_CONTRACT_URL", "")
pytestmark = pytest.mark.skipif(not AUDIT_URL, reason="SECURITY_DATABASE_CONTRACT_URL not explicitly set")


@pytest_asyncio.fixture
async def catalog_connection():
    url = AUDIT_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    connection = await asyncpg.connect(
        url, timeout=15, statement_cache_size=0,
        server_settings={"application_name": "jobrun-security-metadata-audit"},
    )
    try:
        async with connection.transaction(readonly=True):
            await connection.execute("set local statement_timeout = '5s'")
            await connection.execute("set local lock_timeout = '1s'")
            assert await connection.fetchval("show transaction_read_only") == "on"
            yield connection
    finally:
        await connection.close()


async def test_all_public_application_tables_enforce_rls(catalog_connection):
    rows = await catalog_connection.fetch("""
        select c.relname, c.relrowsecurity
        from pg_class c join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public' and c.relkind in ('r', 'p')
    """)
    assert len(rows) >= 38, "Expected JobRun schema, not an empty or unrelated database"
    assert not [row["relname"] for row in rows if not row["relrowsecurity"]]


async def test_browser_roles_have_no_table_administration_privileges(catalog_connection):
    permissions = ["TRUNCATE", "TRIGGER", "REFERENCES"]
    if int(await catalog_connection.fetchval("show server_version_num")) >= 170000:
        permissions.append("MAINTAIN")
    violations = []
    for permission in permissions:
        rows = await catalog_connection.fetch("""
            select c.relname, r.rolname
            from pg_class c join pg_namespace n on n.oid = c.relnamespace
            cross join pg_roles r
            where n.nspname = 'public' and c.relkind in ('r', 'p')
              and r.rolname in ('anon', 'authenticated')
              and has_table_privilege(r.oid, c.oid, $1)
        """, permission)
        violations.extend((row["relname"], row["rolname"], permission) for row in rows)
    assert not violations


async def test_anonymous_role_has_no_public_application_data_grants(catalog_connection):
    violations = await catalog_connection.fetch("""
        select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public' and c.relkind in ('r', 'p', 'v', 'm')
          and (has_table_privilege('anon', c.oid, 'SELECT, INSERT, UPDATE, DELETE')
               or has_any_column_privilege('anon', c.oid, 'SELECT, INSERT, UPDATE'))
    """)
    assert not violations


async def test_private_engine_columns_and_entitlements_are_not_client_writable(catalog_connection):
    hidden = {
        "attempt": ["engine_state", "evaluation"],
        "interview_session": ["state"],
        "session_turn": ["expected_answer_outline", "question_generation_meta"],
        "user_skill_profile": ["knowledge_score", "confidence_score", "engine_state"],
        "user_skill_assessment": ["knowledge_score", "confidence_score"],
    }
    for table, columns in hidden.items():
        for column in columns:
            assert not await catalog_connection.fetchval(
                "select has_column_privilege('authenticated', $1, $2, 'SELECT')", f"public.{table}", column,
            ), f"Client can read {table}.{column}"
    for column in ("plan_tier", "b2b_data_consent", "b2b_consent_version", "b2b_consent_at", "deleted_at"):
        assert not await catalog_connection.fetchval(
            "select has_column_privilege('authenticated', 'public.user_profile', $1, 'UPDATE')", column,
        ), f"Client can write user_profile.{column}"
    assert not await catalog_connection.fetchval("""
        select has_any_column_privilege('authenticated', 'public.jr_members', 'INSERT, UPDATE')
            or has_table_privilege('authenticated', 'public.jr_members', 'DELETE')
    """)


async def test_expected_browser_operations_are_preserved(catalog_connection):
    for table in ("jr_tasks", "jr_practice_entries"):
        for permission in ("SELECT", "INSERT", "UPDATE"):
            assert await catalog_connection.fetchval(
                "select has_table_privilege('authenticated', $1, $2)", f"public.{table}", permission,
            )
    assert await catalog_connection.fetchval("""
        select has_column_privilege('authenticated', 'public.user_profile', 'display_name', 'UPDATE')
            and has_column_privilege('authenticated', 'public.notification', 'opened_at', 'UPDATE')
            and has_column_privilege('authenticated', 'public.attempt', 'answer', 'SELECT')
    """)


async def test_exposed_views_and_definer_functions_do_not_bypass_access_controls(catalog_connection):
    unsafe_views = await catalog_connection.fetch("""
        select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public' and c.relkind in ('v', 'm')
          and (has_table_privilege('anon', c.oid, 'SELECT')
               or has_table_privilege('authenticated', c.oid, 'SELECT'))
          and not coalesce(c.reloptions @> array['security_invoker=true'], false)
    """)
    assert not unsafe_views
    exposed_definers = await catalog_connection.fetch("""
        select p.proname from pg_proc p join pg_namespace n on n.oid = p.pronamespace
        where n.nspname = 'public' and p.prosecdef
          and (has_function_privilege('anon', p.oid, 'EXECUTE')
               or has_function_privilege('authenticated', p.oid, 'EXECUTE'))
    """)
    assert not exposed_definers
    for role in ("anon", "authenticated"):
        assert not await catalog_connection.fetchval(
            "select has_schema_privilege($1, 'jobrun_private', 'USAGE')", role,
        )


async def test_new_postgres_tables_do_not_inherit_browser_maintenance_grants(catalog_connection):
    violations = await catalog_connection.fetch("""
        select x.privilege_type, coalesce(r.rolname, 'PUBLIC') as grantee
        from pg_default_acl d
        join pg_namespace n on n.oid = d.defaclnamespace
        cross join lateral aclexplode(d.defaclacl) x
        left join pg_roles r on r.oid = x.grantee
        where d.defaclrole = (select oid from pg_roles where rolname = 'postgres')
          and n.nspname = 'public' and d.defaclobjtype = 'r'
          and (x.grantee = 0 or r.rolname in ('anon', 'authenticated'))
          and x.privilege_type in ('TRUNCATE', 'TRIGGER', 'REFERENCES', 'MAINTAIN')
    """)
    assert not violations


async def test_application_storage_buckets_remain_private_and_bounded(catalog_connection):
    rows = await catalog_connection.fetch("""
        select id, public, file_size_limit, allowed_mime_types from storage.buckets
        where id in ('practice-answer-images', 'jobrun-task-files', 'question-bank-media')
    """)
    assert len(rows) == 3
    for row in rows:
        assert row["public"] is False
        assert 0 < row["file_size_limit"] <= 10 * 1024 * 1024
        assert row["allowed_mime_types"]
        assert "text/html" not in row["allowed_mime_types"]
        assert "image/svg+xml" not in row["allowed_mime_types"]
