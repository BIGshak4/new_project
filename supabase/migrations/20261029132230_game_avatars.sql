-- Server-owned cosmetic selection and permanent skin entitlements.
create table if not exists public.game_avatar (
  user_id uuid primary key references public.user_profile(id) on delete cascade,
  component text not null default 'mux' check (component in ('and','or','xor','mux','dff')),
  color text not null default 'violet' check (color in ('violet','mint','sky','coral','amber','rose')),
  skin text not null default 'classic' check (skin in ('classic','aurora','circuit','cosmic','gold')),
  owned_skins jsonb not null default '["classic"]'::jsonb
    check (jsonb_typeof(owned_skins) = 'array' and owned_skins ? 'classic'
           and owned_skins <@ '["classic","aurora","circuit","cosmic","gold"]'::jsonb
           and owned_skins ? skin)
);
comment on table public.game_avatar is
  'One cosmetic avatar per account. Entitlements and coin debits are committed together by the backend. Job_Run shirt is fixed.';
alter table public.game_avatar enable row level security;
revoke all on public.game_avatar from public, anon, authenticated;
grant select on public.game_avatar to authenticated;
grant all on public.game_avatar to service_role;
drop policy if exists "game_avatar: read own" on public.game_avatar;
create policy "game_avatar: read own" on public.game_avatar
  for select to authenticated using (user_id = (select auth.uid()));
