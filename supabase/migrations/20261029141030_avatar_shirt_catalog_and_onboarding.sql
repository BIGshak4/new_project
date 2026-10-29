-- Preserve all existing avatars and entitlements while expanding the fixed shirt catalog.
alter table public.game_avatar drop constraint if exists game_avatar_skin_check;
alter table public.game_avatar drop constraint if exists game_avatar_check;

alter table public.game_avatar add constraint game_avatar_skin_check check (
  skin in ('classic','aurora','circuit','cosmic','gold','negative_feedback','works_on_my_machine',
           'binary_people','gate_keeper','sleep_not_found','resistance_futile')
);
alter table public.game_avatar add constraint game_avatar_check check (
  jsonb_typeof(owned_skins) = 'array' and owned_skins ? 'classic'
  and owned_skins <@ '["classic","aurora","circuit","cosmic","gold","negative_feedback","works_on_my_machine","binary_people","gate_keeper","sleep_not_found","resistance_futile"]'::jsonb
  and owned_skins ? skin
);

-- Existing customized rows are already onboarded; newly inserted rows are not.
alter table public.game_avatar add column if not exists onboarding_completed boolean not null default true;
alter table public.game_avatar alter column onboarding_completed set default false;
comment on column public.game_avatar.onboarding_completed is
  'Server-owned completion of optional free character setup. Existing avatar selections are retained.';
