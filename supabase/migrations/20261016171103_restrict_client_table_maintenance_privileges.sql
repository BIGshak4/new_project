-- Browser roles need only explicitly granted row/column operations. Legacy
-- default grants also left table administration privileges on 28 tables.
-- TRUNCATE and REFERENCES do not obey RLS; none is used by the browser client.
-- Preserve all SELECT/INSERT/UPDATE/DELETE and column-level grants and policies.
revoke truncate, references, trigger on all tables in schema public
  from public, anon, authenticated;

-- Application migrations are created by postgres. Prevent these grants from
-- returning when a later migration creates another public application table.
alter default privileges for role postgres in schema public
  revoke truncate, references, trigger on tables from public, anon, authenticated;

-- MAINTAIN is a PostgreSQL 17+ table privilege. Keep the migration compatible
-- with earlier supported Supabase PostgreSQL versions too.
do $$
begin
  if current_setting('server_version_num')::integer >= 170000 then
    execute 'revoke maintain on all tables in schema public from public, anon, authenticated';
    execute 'alter default privileges for role postgres in schema public revoke maintain on tables from public, anon, authenticated';
  end if;
end $$;
