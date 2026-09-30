-- Honest provenance for imported founder-supplied content (not licensed or formally reviewed).
alter type public.question_origin add value if not exists 'user_supplied';

-- Backend signs only allowlisted question paths, after checking pilot access and solution exposure.
-- No anon/authenticated read or write policies are added for this private bucket.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('question-bank-media', 'question-bank-media', false, 10485760,
        array['image/png', 'text/plain', 'application/json'])
on conflict (id) do nothing;
