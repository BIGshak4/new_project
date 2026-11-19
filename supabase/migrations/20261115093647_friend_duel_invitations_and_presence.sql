create table public.user_presence (
  user_id uuid primary key references public.user_profile(id) on delete cascade,
  last_seen_at timestamptz not null
);

alter table public.user_presence enable row level security;
revoke all on public.user_presence from public, anon, authenticated;
grant select, insert, update, delete on public.user_presence to service_role;

-- Only open targeted invites appear in a friend's inbox. Ordinary code-based invites have no recipient.
create index duel_open_invitation_recipient on public.duel
  ((meta ->> 'invited_friend_id'), created_at desc) where status = 'open';
