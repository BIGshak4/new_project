# Interview history and fundamentals quiz — 2026-11-05

Previous mock interviews now have a separate Delete button and inline confirmation. A successful authenticated DELETE removes the entry from personal history permanently across reloads. The server records `interview_session.deleted_at`, independently of the scoring state. List queries filter it before pagination; direct reads and subsequent user actions return 404. Repeating the same deletion succeeds for its owner, while missing or foreign interviews return 404. Accepted background evaluations may finish, and their earned learning evidence and daily usage remain intact.

The history UI keeps rows visible when deletion fails, supports cancellation and retry, and moves focus to the history heading after success. Deletion is bound to the account that opened the workspace. Browser verification used simulated history records and errors; no real user interview was deleted during validation.

The short-question workspace now has a Quiz button. Its centered topic dialog offers all eight existing topics, a mixed-state Select all checkbox, available-question count, and a disabled start action for an insufficient pool. It draws ten distinct questions uniformly from the entire selected topic pool, independently of search and completion filters. The resulting workspace view shows all ten questions consecutively, each with its own initially closed solution and reporting actions. This is self-study and does not assign a grade or change saved completion records.

Quiz IDs remain fixed while switching languages. Browser Back returns to the cards; Forward restores the same quiz. New quiz replaces the current quiz entry. History data is checked against the signed-in account, existing question IDs and selected topics. Diagrams share the existing renderer with normal short questions.

Checks include backend ownership, repeated deletion, transaction rollback, deletion before pagination, concurrent evaluation, and evidence/usage preservation; frontend account-change refusal; quiz selection/history validation; and browser interactions with actual components using local API stubs. Hebrew/English and light/dark layouts were inspected at desktop and 388 CSS-pixel mobile widths. Local screenshots are under `.impeccable/review/history-quiz-20261105/`. Temporary browser-check routes were removed before the production build.

The live schema received the nullable deletion marker before backend deployment. No existing interview was marked deleted during the migration, and no authentication or RLS permissions changed.
