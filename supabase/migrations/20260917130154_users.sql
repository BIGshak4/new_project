-- ============================================================================
-- 0300  Users
-- Source: src/Data_Models.md §8.1 (User)
--
-- Decision: Supabase Auth. `user_profile.id` is the same UUID as `auth.users.id`.
-- Email and the auth subject live in auth.users, so `email` and
-- `auth_provider_id` from the spec are not duplicated here. A trigger creates
-- the profile row the moment a user signs up.
-- ============================================================================

create table public.user_profile (
  id                          uuid primary key references auth.users(id) on delete cascade,
  display_name                varchar(120),
  experience_years            smallint check (experience_years >= 0),
  seniority_self_assessed     public.seniority,
  background                  jsonb not null default '{}'::jsonb,
  interface_language          public.content_language not null default 'en',
  practice_language           public.content_language not null default 'en',
  target_interview_date       date,
  available_minutes_per_day   smallint check (available_minutes_per_day between 0 and 1440),
  diagnostic_completed_at     timestamptz,                    -- set by the backend when the signup diagnostic is done
  notification_prefs          jsonb not null default '{"enabled": false}'::jsonb,
  target_families             text[]  not null default '{}',
  target_role_ids             uuid[]  not null default '{}',
  target_company_ids          uuid[]  not null default '{}',
  plan_tier                   public.plan_tier not null default 'free',
  b2b_data_consent            boolean not null default false,
  b2b_consent_version         varchar(20),
  b2b_consent_at              timestamptz,
  locale                      varchar(10) not null default 'en-US',
  created_at                  timestamptz not null default now(),
  updated_at                  timestamptz not null default now(),
  deleted_at                  timestamptz,

  constraint user_profile_background_is_object_chk   check (jsonb_typeof(background) = 'object'),
  constraint user_profile_notif_prefs_is_object_chk  check (jsonb_typeof(notification_prefs) = 'object'),
  constraint user_profile_target_families_chk        check (target_families <@ array['hardware', 'software', 'cross_family']::text[]),
  -- Consent must carry a version and a timestamp when granted (Data_Models §8.1, Architecture §6).
  constraint user_profile_consent_chk check (
    b2b_data_consent = false or (b2b_consent_version is not null and b2b_consent_at is not null)
  )
);

comment on table  public.user_profile is 'Per-user profile, 1:1 with auth.users (Data_Models §8.1). Created by trigger on signup.';
comment on column public.user_profile.deleted_at is 'Soft delete. Setting it (or hard-deleting the row) anonymizes evaluation_metrics via the trigger defined in 0800_evaluation.sql (Data_Models §18).';
comment on column public.user_profile.diagnostic_completed_at is 'When the 8-12 item signup diagnostic finished (AI_Engine_Spec §4.11). Progress rewards count only attempts after this.';

create trigger user_profile_set_updated_at
  before update on public.user_profile
  for each row execute function public.set_updated_at();

-- ---- Create the profile row on signup -------------------------------------------
-- Language preferences can be passed in signup metadata; anything invalid falls
-- back to 'en' so a bad value can never block registration.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  meta          jsonb := coalesce(new.raw_user_meta_data, '{}'::jsonb);
  ui_lang       public.content_language := 'en';
  practice_lang public.content_language := 'en';
begin
  if meta ->> 'interface_language' in ('he', 'en') then
    ui_lang := (meta ->> 'interface_language')::public.content_language;
  end if;
  if meta ->> 'practice_language' in ('he', 'en') then
    practice_lang := (meta ->> 'practice_language')::public.content_language;
  end if;

  insert into public.user_profile (id, display_name, interface_language, practice_language, locale)
  values (
    new.id,
    -- capped at the column length and never the empty string, so a bad value cannot abort signup
    nullif(left(coalesce(
      nullif(meta ->> 'display_name', ''),
      nullif(meta ->> 'full_name', ''),
      split_part(coalesce(new.email, ''), '@', 1)
    ), 120), ''),
    ui_lang,
    practice_lang,
    case when ui_lang = 'he' then 'he-IL' else 'en-US' end
  )
  on conflict (id) do nothing;

  return new;
end;
$$;

revoke execute on function public.handle_new_user() from public, anon, authenticated;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
