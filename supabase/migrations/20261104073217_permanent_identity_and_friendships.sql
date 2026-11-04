-- Permanent account identity and explicit friendship requests. Existing profile data is preserved.
-- Username is deliberately nullable only for legacy accounts until their one-time claim.
create schema if not exists jobrun_private;
revoke all on schema jobrun_private from public, anon, authenticated;

alter table public.user_profile
  add column username text,
  add column username_key text generated always as (lower(normalize(username, NFKC))) stored,
  add column friend_code text;

create unique index user_profile_username_key_unique on public.user_profile(username_key) where username_key is not null;
create unique index user_profile_friend_code_unique on public.user_profile(friend_code) where friend_code is not null;

create function jobrun_private.username_reason(candidate text)
returns text language plpgsql immutable set search_path = '' as $$
declare
  value text := lower(normalize(btrim(coalesce(candidate, '')), NFKC));
  part text;
  candidate_part text;
  banned text;
  parts text[];
begin
  if length(value) not between 3 and 24 or value !~ '^[a-zא-ת0-9_]+$' or value !~ '[a-zא-ת]' then
    return 'invalid';
  end if;
  if value = any(array['admin','administrator','moderator','support','system','jobrun','muxi','מוקסי','תמיכה','מנהל']) then
    return 'invalid';
  end if;
  parts := regexp_split_to_array(value, '_+') || array[replace(value, '_', '')];
  foreach part in array parts loop
    foreach candidate_part in array array[part, regexp_replace(part, '^[0-9]+|[0-9]+$', '', 'g')] loop
      candidate_part := translate(candidate_part, '01345789', 'oieastbg');
      -- Unambiguous profane stems remain disallowed when attached to a name. Ambiguous short tokens
      -- (ass/dick/cock/fag) stay whole-token-only so ordinary names such as Dickinson are not rejected.
      foreach banned in array array['fuck','faggot','nigger','nigga','heilhitler','שרמוט','בןזונה','בתזונה',
                                    'כוסאמא','כוסאמק','מזדיין','מזדיינת','לזיין'] loop
        if candidate_part ~ regexp_replace(banned, '(.)', '\1+', 'g') then return 'offensive'; end if;
      end loop;
      foreach banned in array array[
      'fuck','fucker','fucking','fuckyou','fuckoff','motherfucker','fck','fuk','fcuk','phuck',
      'shit','bullshit','asshole','bastard','bitch','cunt','dick','cock','pussy','whore','slut',
      'nigger','nigga','faggot','fag','retard','nazi','hitler','heilhitler','kkk',
      'זין','כוס','זונה','שרמוטה','מניאק','בןזונה','בתזונה','בןשרמוטה','כוסאמא','כוסאמאשלך',
      'כוסאמק','נאצי','נאצים','היטלר','חרא','לזיין','מזדיין','מזדיינת','זיונים'
      ] loop
        -- Whole-name matching permits ordinary substrings, while repeated letters do not evade a banned token.
        if candidate_part ~ ('^' || regexp_replace(banned, '(.)', '\1+', 'g') || '$') then return 'offensive'; end if;
      end loop;
    end loop;
  end loop;
  return null;
end;
$$;
revoke all on function jobrun_private.username_reason(text) from public, anon, authenticated;

create function jobrun_private.identity_code_candidate()
returns text language sql volatile set search_path = '' as $$
  select upper(substr(replace(pg_catalog.gen_random_uuid()::text, '-', ''), 1, 8));
$$;
revoke all on function jobrun_private.identity_code_candidate() from public, anon, authenticated;

create function jobrun_private.allocate_friend_code()
returns text language plpgsql volatile security definer set search_path = '' as $$
declare candidate text;
begin
  -- Held through the profile INSERT/UPDATE: two concurrent signups cannot select the same free code.
  -- The unique index remains an independent final constraint; random collisions retry rather than abort signup.
  perform pg_advisory_xact_lock(hashtextextended('jobrun:permanent-friend-code', 0));
  for attempt in 1..128 loop
    candidate := jobrun_private.identity_code_candidate();
    if not exists(select 1 from public.user_profile p where p.friend_code = candidate) then return candidate; end if;
  end loop;
  raise exception 'friend_code_allocation_failed' using errcode = '54000';
end;
$$;
revoke all on function jobrun_private.allocate_friend_code() from public, anon, authenticated;

create function jobrun_private.guard_profile_identity()
returns trigger language plpgsql security definer set search_path = '' as $$
declare meta_username text; reason text;
begin
  if tg_op = 'INSERT' then
    -- Preserve public.handle_new_user and the existing backend's profile-provision fallback.
    -- Future auth rows have already passed guard_auth_identity; legacy rows may still have no username.
    select u.raw_user_meta_data ->> 'username' into meta_username from auth.users u where u.id = new.id;
    if meta_username is not null and jobrun_private.username_reason(meta_username) is null then
      new.username := normalize(btrim(meta_username), NFKC);
    end if;
    new.friend_code := jobrun_private.allocate_friend_code();
  else
    if new.id is distinct from old.id then raise exception 'identity_immutable' using errcode = '23514'; end if;
    if old.friend_code is not null and new.friend_code is distinct from old.friend_code then
      raise exception 'friend_code_immutable' using errcode = '23514';
    end if;
    if old.username is not null and new.username is distinct from old.username then
      raise exception 'username_immutable' using errcode = '23514';
    end if;
  end if;
  if new.username is not null then
    reason := jobrun_private.username_reason(new.username);
    if reason is not null then raise exception 'username_%', reason using errcode = '23514'; end if;
    new.username := normalize(btrim(new.username), NFKC);
  end if;
  return new;
end;
$$;
revoke all on function jobrun_private.guard_profile_identity() from public, anon, authenticated;
create trigger user_profile_identity_guard before insert or update on public.user_profile
for each row execute function jobrun_private.guard_profile_identity();

-- Every current auth account receives a code, including old accounts lacking a profile row.
insert into public.user_profile(id)
select u.id from auth.users u where not exists(select 1 from public.user_profile p where p.id = u.id);
do $$
declare profile record;
begin
  for profile in select id from public.user_profile where friend_code is null order by id loop
    update public.user_profile set friend_code = jobrun_private.allocate_friend_code() where id = profile.id;
  end loop;
end;
$$;
alter table public.user_profile alter column friend_code set not null;
alter table public.user_profile add constraint user_profile_friend_code_format check(friend_code ~ '^[0-9A-F]{8}$');
alter table public.user_profile add constraint user_profile_username_format check(username is null or (
  username = normalize(btrim(username), NFKC) and length(username) between 3 and 24
  and username ~ '^[A-Za-zא-ת0-9_]+$' and username ~ '[A-Za-zא-ת]'));
revoke update(username, username_key, friend_code) on public.user_profile from public, anon, authenticated;

create function jobrun_private.guard_auth_identity()
returns trigger language plpgsql security definer set search_path = '' as $$
declare chosen text; claimed text; reason text;
begin
  chosen := new.raw_user_meta_data ->> 'username';
  if tg_op = 'INSERT' then
    if chosen is null then raise exception 'username_required' using errcode = '23514'; end if;
    reason := jobrun_private.username_reason(chosen);
    if reason is not null then raise exception 'username_%', reason using errcode = '23514'; end if;
    new.raw_user_meta_data := jsonb_set(coalesce(new.raw_user_meta_data, '{}'::jsonb), '{username}',
                                      to_jsonb(normalize(btrim(chosen), NFKC)), true);
  elsif (new.raw_user_meta_data ->> 'username') is distinct from (old.raw_user_meta_data ->> 'username') then
    select p.username into claimed from public.user_profile p where p.id = new.id;
    if claimed is not null and normalize(btrim(coalesce(chosen, '')), NFKC) is distinct from claimed then
      raise exception 'username_immutable' using errcode = '23514';
    end if;
  end if;
  return new;
end;
$$;
revoke all on function jobrun_private.guard_auth_identity() from public, anon, authenticated;
create trigger jobrun_auth_identity_guard before insert or update of raw_user_meta_data on auth.users
for each row execute function jobrun_private.guard_auth_identity();

create table public.friendship (
  id uuid primary key default gen_random_uuid(),
  requester_id uuid not null references public.user_profile(id) on delete cascade,
  recipient_id uuid not null references public.user_profile(id) on delete cascade,
  status text not null default 'pending' check(status in ('pending', 'accepted')),
  created_at timestamptz not null default now(),
  accepted_at timestamptz,
  constraint friendship_not_self check(requester_id <> recipient_id),
  constraint friendship_accepted_stamp check((status = 'accepted') = (accepted_at is not null))
);
create unique index friendship_pair_unique on public.friendship(least(requester_id, recipient_id), greatest(requester_id, recipient_id));
create index friendship_requester on public.friendship(requester_id, status, created_at);
create index friendship_recipient on public.friendship(recipient_id, status, created_at);
alter table public.friendship enable row level security;
revoke all on public.friendship from public, anon, authenticated;
grant select on public.friendship to authenticated;
grant select, insert, update, delete on public.friendship to service_role;
create policy "participants read own friendship" on public.friendship for select to authenticated
using(requester_id = (select auth.uid()) or recipient_id = (select auth.uid()));

comment on column public.user_profile.username is 'Permanent once claimed; old accounts may claim once, future signup requires it.';
comment on column public.user_profile.friend_code is 'Permanent random uppercase eight-hex friend code. Not an authentication secret.';
comment on table public.friendship is 'Backend-managed explicit request/accept friendships. No emails, balances or inventory exposed.';
