# SEC-008 — Browser database roles held unnecessary table-administration privileges

- **Severity:** Medium configuration exposure. Whole-table authority increases blast radius; no public HTTP route executing arbitrary SQL or remote table wipe was demonstrated.
- **Status:** Database migration deployed and metadata verified on 2026-10-16.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** Live public-schema grants and default privileges before this migration; migration is included with the audit source changes.

## Problem and impact

Metadata showed unnecessary authenticated-role maintenance privileges on 28 of 38 public tables: `TRUNCATE`, `REFERENCES`, `TRIGGER` and PostgreSQL 17 `MAINTAIN`. Row security does not constrain whole-table operations such as TRUNCATE/REFERENCES. These rights were unnecessary for the browser's normal row operations. A dangerous grant is not, by itself, proof that the normal Data API exposes a way to invoke it.

## Safe reproduction

Use PostgreSQL catalog/`has_table_privilege` queries only. Do not truncate, alter or exercise administrative operations against application tables. Inspect default ACLs as well as existing tables.

## Exact remediation

`supabase/migrations/20261016171103_restrict_client_table_maintenance_privileges.sql` revokes the unused administration rights from PUBLIC, `anon` and `authenticated`, including defaults for new public tables created by `postgres`. MAINTAIN revocation is conditional on supported PostgreSQL versions. Intended SELECT/INSERT/UPDATE/DELETE and column grants, table policies and owner/service operations are preserved.

## Verification

Supabase reported successful production migration application. Post-change metadata found **zero** affected tables, with **38/38** public tables still enforcing RLS. Eight read-only contract groups passed through the authorized database tool, checking grants/defaults, hidden engine fields, membership protections, expected browser operations, private buckets and exposed privileged objects. Before/after comparison confirmed policy/column ACL preservation.

`backend/tests/test_security_database_contract.py` records repeatable opt-in checks. Pytest cases skipped without an explicit audit URL are not counted as passed; the stated checks were executed separately through the database tool.

## Remaining work

Keep these checks in future migration reviews and review default privileges for any additional table-creating roles. No data-destructive proof is required or authorized to validate the revocation.

## References

[PostgreSQL row-security scope](https://www.postgresql.org/docs/17/ddl-rowsecurity.html), [table privileges](https://www.postgresql.org/docs/17/ddl-priv.html).
