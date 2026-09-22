-- "On trial": a question the founders put in front of pilot users to check it live (hints, follow-up,
-- feedback, next-question suggestion, mock interview) before it is formally published. Served like a
-- published question and marked as trial in the app; publishing still requires the review fields.
-- Shaked, 2026-09-22.

alter type public.question_status add value if not exists 'trial' after 'in_review';

comment on type public.question_status is
  'draft -> in_review -> trial (checked live by the founders, served to pilot users, badged) -> published; withheld/retired take a question out of service';
